"""S3 Vectors — the cheap managed vector store this course uses on AWS.

Why this and not OpenSearch Serverless: an OpenSearch Serverless *classic*
collection bills a 2-OCU minimum, roughly $350/month, whether you query it or
not. S3 Vectors costs $0.06/GB-month plus $2.50 per million queries. At this
course's scale that is under ten cents a month — effectively free.

(OpenSearch Serverless NextGen, GA May 2026, has no OCU minimum and scales to
zero after 10 minutes idle. If quick-create now provisions NextGen, the classic
warning is out of date — check on Day 4 and write down what you find.)

Trade-offs you must be able to state, because a client will ask:
  - semantic (dense) search only — no hybrid BM25, so Day 14's hybrid lane
    needs a different store or a client-side merge
  - float32 vectors only — no binary quantisation
  - 1 KB of custom metadata per vector; hierarchical chunking can exceed it
  - cold-start latency under a second, warm around 100ms

The one cost gotcha: PUT bills a 128 KB minimum per request. Uploading 2,000
vectors one at a time costs ~$0.05; batched it costs ~$0.002. Always batch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from .settings import settings

MAX_BATCH = 500  # keep requests comfortably under service limits


def _client():
    import boto3

    return boto3.Session(
        profile_name=settings.aws_profile or None,
        region_name=settings.aws_region,
    ).client("s3vectors")


@dataclass
class VectorHit:
    key: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        return self.metadata.get("text", "")


class S3VectorStore:
    """Same interface as the Day 3 SimpleVectorStore, backed by S3 Vectors.

    Deliberate: every lab from Day 4 onward can swap between the two by changing
    one line, which is what makes the local-vs-managed comparison honest.
    """

    def __init__(
        self,
        bucket: str,
        index: str = "corpus",
        dimensions: int = 1024,
        distance: str = "cosine",
    ) -> None:
        self.bucket = bucket
        self.index = index
        self.dimensions = dimensions
        self.distance = distance
        self._c = _client()

    # ── lifecycle ───────────────────────────────────────────────────────────
    def create(self, non_filterable: Sequence[str] = ("text",)) -> None:
        """Create bucket and index if absent.

        `non_filterable` matters: metadata keys listed here are stored and
        returned but not indexed for filtering. Put your chunk text here — it is
        large, you never filter on it, and indexing it wastes the 1 KB budget.
        """
        try:
            self._c.create_vector_bucket(vectorBucketName=self.bucket)
        except self._c.exceptions.ConflictException:
            pass

        try:
            self._c.create_index(
                vectorBucketName=self.bucket,
                indexName=self.index,
                dataType="float32",
                dimension=self.dimensions,
                distanceMetric=self.distance,
                metadataConfiguration={"nonFilterableMetadataKeys": list(non_filterable)},
            )
        except self._c.exceptions.ConflictException:
            pass

    def delete(self) -> None:
        """Teardown. Indexes must go before the bucket."""
        try:
            self._c.delete_index(vectorBucketName=self.bucket, indexName=self.index)
        except Exception:
            pass
        try:
            self._c.delete_vector_bucket(vectorBucketName=self.bucket)
        except Exception:
            pass

    # ── write ───────────────────────────────────────────────────────────────
    def add(self, items: Iterable[tuple[str, list[float], dict]]) -> int:
        """items: (key, vector, metadata). Batched — see the PUT minimum above."""
        batch: list[dict] = []
        n = 0
        for key, vec, meta in items:
            batch.append(
                {
                    "key": key,
                    "data": {"float32": [float(x) for x in vec]},
                    "metadata": meta,
                }
            )
            if len(batch) >= MAX_BATCH:
                self._flush(batch)
                n += len(batch)
                batch = []
        if batch:
            self._flush(batch)
            n += len(batch)
        return n

    def _flush(self, batch: list[dict]) -> None:
        self._c.put_vectors(
            vectorBucketName=self.bucket, indexName=self.index, vectors=batch
        )

    # ── read ────────────────────────────────────────────────────────────────
    def search(
        self,
        query_vector: Sequence[float],
        k: int = 5,
        filter: dict | None = None,
    ) -> list[VectorHit]:
        req: dict[str, Any] = {
            "vectorBucketName": self.bucket,
            "indexName": self.index,
            "queryVector": {"float32": [float(x) for x in query_vector]},
            "topK": k,
            "returnMetadata": True,
            "returnDistance": True,
        }
        if filter:
            req["filter"] = filter

        resp = self._c.query_vectors(**req)
        hits: list[VectorHit] = []
        for v in resp.get("vectors", []):
            # The API returns DISTANCE, not similarity. For cosine distance,
            # similarity = 1 - distance. Forgetting this inverts your ranking
            # and produces a system that confidently returns the worst matches.
            dist = v.get("distance", 0.0)
            score = 1.0 - dist if self.distance == "cosine" else -dist
            hits.append(VectorHit(key=v["key"], score=score, metadata=v.get("metadata", {})))
        return hits

    def count(self) -> int:
        n, token = 0, None
        while True:
            kw = {"vectorBucketName": self.bucket, "indexName": self.index, "maxResults": 500}
            if token:
                kw["nextToken"] = token
            r = self._c.list_vectors(**kw)
            n += len(r.get("vectors", []))
            token = r.get("nextToken")
            if not token:
                break
        return n


def estimate_cost(n_vectors: int, dimensions: int, queries_per_month: int) -> dict:
    """Back-of-envelope S3 Vectors cost. Use this in client conversations.

    Rates are August 2026, us-east-1 — refresh before quoting them.
    """
    gb = (n_vectors * dimensions * 4) / (1024**3)
    storage = gb * 0.06
    puts_batched = max(gb, 0.000122) * 0.20  # 128 KB minimum per PUT
    puts_single = (n_vectors * 131072) / (1024**3) * 0.20
    queries = queries_per_month / 1_000_000 * 2.50
    return {
        "vectors": n_vectors,
        "storage_gb": round(gb, 4),
        "storage_usd_month": round(storage, 4),
        "ingest_usd_batched": round(puts_batched, 4),
        "ingest_usd_one_at_a_time": round(puts_single, 4),
        "query_usd_month": round(queries, 4),
        "total_usd_month": round(storage + queries, 4),
        "note": "Batching cuts ingest cost ~25x at this scale. Rates as of Aug 2026.",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(estimate_cost(2_000, 1024, 5_000), indent=2))
    print(json.dumps(estimate_cost(2_000_000, 1024, 5_000_000), indent=2))
