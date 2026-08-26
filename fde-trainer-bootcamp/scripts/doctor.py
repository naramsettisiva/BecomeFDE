#!/usr/bin/env python3
"""Environment check. Run this on Day 1 and any morning something feels broken.

    python scripts/doctor.py

Green everywhere = start the lab. Anything red = fix it first.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

OK, BAD, MEH = "\033[32m  OK \033[0m", "\033[31m FAIL\033[0m", "\033[33m WARN\033[0m"
results: list[tuple[str, str, str]] = []


def check(name: str, fn, required: bool = True) -> None:
    try:
        detail = fn() or ""
        results.append((OK, name, str(detail)))
    except Exception as exc:  # noqa: BLE001
        results.append((BAD if required else MEH, name, f"{type(exc).__name__}: {exc}"))


# --------------------------------------------------------------- python + deps
def _python():
    v = sys.version_info
    assert v >= (3, 11), f"need Python >= 3.11, found {v.major}.{v.minor}"
    return f"{v.major}.{v.minor}.{v.micro}"


def _venv():
    assert sys.prefix != sys.base_prefix, "not inside a virtualenv — `source .venv/bin/activate`"
    return Path(sys.prefix).name


def _pkg(mod: str):
    def inner():
        m = importlib.import_module(mod)
        return getattr(m, "__version__", "installed")

    return inner


# --------------------------------------------------------------- config
def _dotenv():
    assert (ROOT / ".env").exists(), ".env missing — `cp .env.example .env`"
    return ".env present"


def _settings():
    from fdekit import settings

    return f"backend={settings.fdekit_backend} chat={settings.chat_model}"


# --------------------------------------------------------------- services
def _ollama():
    import httpx

    from fdekit import settings

    r = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
    r.raise_for_status()
    names = [m["name"] for m in r.json().get("models", [])]
    assert names, "ollama running but no models pulled — `ollama pull llama3.1:8b`"
    return ", ".join(names[:4])


def _local_chat():
    from fdekit import chat

    out = chat("Reply with exactly: pong", backend="local", max_tokens=10)
    return out.strip()[:40]


def _local_embed():
    from fdekit import embed

    v = embed("hello world", backend="local")
    return f"dim={len(v[0])}"


def _openai_key():
    from fdekit import settings

    assert settings.openai_api_key, "OPENAI_API_KEY empty (only needed for [PAID] labs)"
    return "key present"


def _anthropic_key():
    from fdekit import settings

    assert settings.anthropic_api_key, "ANTHROPIC_API_KEY empty (only needed for [PAID] labs)"
    return "key present"


def _git():
    assert (ROOT / ".git").exists(), "not a git repo — run scripts/setup.sh"
    return "repo initialised"


# --------------------------------------------------------------- aws lane
def _boto():
    import boto3

    return boto3.__version__


def _aws_identity():
    import boto3

    from fdekit import settings

    sess = boto3.Session(
        profile_name=settings.aws_profile or None, region_name=settings.aws_region
    )
    ident = sess.client("sts").get_caller_identity()
    arn = ident["Arn"]
    assert not arn.endswith(":root"), "using ROOT credentials — see labs/aws/AWS_SETUP.md"
    return f"{ident['Account']} as {arn.rsplit('/', 1)[-1]}"


def _bedrock_access():
    import boto3

    from fdekit import settings

    sess = boto3.Session(
        profile_name=settings.aws_profile or None, region_name=settings.aws_region
    )
    ids = [
        m["modelId"]
        for m in sess.client("bedrock").list_foundation_models()["modelSummaries"]
    ]
    missing = [
        w for w in ("nova-micro", "nova-lite", "titan-embed-text-v2") if not any(w in i for i in ids)
    ]
    assert not missing, f"no access to {', '.join(missing)} — Bedrock console > Model access"
    return f"{len(ids)} models visible"


def _bedrock_roundtrip():
    from fdekit import chat

    out = chat(
        "Reply with exactly: pong",
        backend="bedrock",
        model="amazon.nova-micro-v1:0",
        max_tokens=8,
    )
    return out.strip()[:40]


def _s3vectors():
    import boto3

    from fdekit import settings

    sess = boto3.Session(
        profile_name=settings.aws_profile or None, region_name=settings.aws_region
    )
    r = sess.client("s3vectors").list_vector_buckets(maxResults=1)
    return f"{len(r.get('vectorBuckets', []))} bucket(s)"


# --------------------------------------------------------------- run
if __name__ == "__main__":
    print(f"\n  FDE Trainer Bootcamp — environment check\n  {ROOT}\n")

    check("python >= 3.11", _python)
    check("virtualenv active", _venv)
    check("git repo", _git)
    check(".env file", _dotenv)
    check("fdekit settings", _settings)

    for mod in ["numpy", "pydantic", "openai", "httpx", "rich"]:
        check(f"pkg {mod}", _pkg(mod))
    for mod in ["langchain", "langgraph", "chromadb", "fastapi", "ragas"]:
        check(f"pkg {mod}", _pkg(mod), required=False)

    check("ollama service", _ollama)
    check("local chat round-trip", _local_chat)
    check("local embeddings", _local_embed)

    check("OPENAI_API_KEY", _openai_key, required=False)
    check("ANTHROPIC_API_KEY", _anthropic_key, required=False)

    # AWS lane — warnings only, so the core lane still passes without an account.
    print("\n  --- aws lane (optional until Day 1's AWS block) ---")
    check("pkg boto3", _boto, required=False)
    check("aws identity", _aws_identity, required=False)
    check("bedrock model access", _bedrock_access, required=False)
    check("bedrock round-trip", _bedrock_roundtrip, required=False)
    check("s3 vectors API", _s3vectors, required=False)

    width = max(len(n) for _, n, _ in results)
    for status, name, detail in results:
        print(f"  [{status}] {name.ljust(width)}  {detail}")

    failures = sum(1 for s, _, _ in results if s == BAD)
    warns = sum(1 for s, _, _ in results if s == MEH)
    print(f"\n  {len(results) - failures - warns} ok · {warns} warn · {failures} fail\n")
    if failures:
        print("  Fix the FAIL lines before starting today's lab.\n")
    sys.exit(1 if failures else 0)
