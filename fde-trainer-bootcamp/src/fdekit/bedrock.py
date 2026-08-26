"""Amazon Bedrock behind the same seam as everything else.

The point of Day 1's `chat()` seam was that swapping providers should be one env
var. This file is that promise being kept: set FDEKIT_BACKEND=bedrock and every
lab from Day 1 to Day 24 runs on AWS with no other change.

Two APIs matter here:

  Converse  — one message shape across every Bedrock model, with native tool use.
              Use this. It is why you do not need per-model request builders.
  InvokeModel — the older per-model-JSON API. You will meet it in client code and
              in most blog posts. Know it exists; do not write new code with it.

Cost note: default to Nova Micro/Lite. Claude on Bedrock is the same model you get
from Anthropic directly and roughly 30x the price of Nova Lite — reserve it for
judging and demos. See labs/aws/AWS_COST_DISCIPLINE.md.
"""

from __future__ import annotations

import json
from typing import Any, Iterator, Sequence

from .cost import track
from .settings import settings

Message = dict[str, Any]

# ── model ids ───────────────────────────────────────────────────────────────
# Verify these in the console: `make aws-models`. Bedrock model IDs change more
# often than people expect, and a stale ID is a confusing 404 rather than a clear
# error. Note also that region-prefixed inference profiles (us./eu./global.) are
# required for some models — if a bare ID 404s, try the profile form.
NOVA_MICRO = "amazon.nova-micro-v1:0"
NOVA_LITE = "amazon.nova-lite-v1:0"
NOVA_PRO = "amazon.nova-pro-v1:0"
TITAN_EMBED = "amazon.titan-embed-text-v2:0"


def _session():
    import boto3

    return boto3.Session(
        profile_name=settings.aws_profile or None,
        region_name=settings.aws_region,
    )


def _runtime():
    return _session().client("bedrock-runtime")


# ── chat ────────────────────────────────────────────────────────────────────
def _to_converse(messages: Sequence[Message]) -> list[dict]:
    """OpenAI-shaped messages -> Bedrock Converse content blocks.

    Converse wants content as a list of typed blocks, and it does NOT accept a
    'system' role inside messages — system goes in its own top-level parameter.
    Getting this wrong produces a ValidationException that does not say so.
    """
    out: list[dict] = []
    for m in messages:
        if m.get("role") == "system":
            continue  # caller must pass system= separately
        content = m["content"]
        blocks = [{"text": content}] if isinstance(content, str) else content
        out.append({"role": m["role"], "content": blocks})
    return out


def chat(
    prompt_or_messages: str | Sequence[Message],
    *,
    system: str | None = None,
    model: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
    tools: list[dict] | None = None,
    **kwargs: Any,
) -> str | dict:
    """Return assistant text, or the full response dict when tools are supplied."""
    model = model or settings.bedrock_chat_model
    msgs = (
        [{"role": "user", "content": prompt_or_messages}]
        if isinstance(prompt_or_messages, str)
        else list(prompt_or_messages)
    )
    # A system message passed inline is a common mistake — rescue it rather than 400.
    if system is None:
        inline = [m for m in msgs if m.get("role") == "system"]
        if inline:
            system = inline[0]["content"]

    req: dict[str, Any] = {
        "modelId": model,
        "messages": _to_converse(msgs),
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature},
    }
    if system:
        req["system"] = [{"text": system}]
    if tools:
        req["toolConfig"] = {"tools": tools}
    req.update(kwargs)

    resp = _runtime().converse(**req)

    usage = resp.get("usage", {})
    track(model, usage.get("inputTokens", 0), usage.get("outputTokens", 0))

    if tools:
        return resp  # caller inspects stopReason / toolUse blocks

    blocks = resp["output"]["message"]["content"]
    return "".join(b.get("text", "") for b in blocks)


def chat_stream(
    prompt_or_messages: str | Sequence[Message],
    *,
    system: str | None = None,
    model: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> Iterator[str]:
    """Yield text deltas. Used by the Day 15 streaming service."""
    model = model or settings.bedrock_chat_model
    msgs = (
        [{"role": "user", "content": prompt_or_messages}]
        if isinstance(prompt_or_messages, str)
        else list(prompt_or_messages)
    )
    req: dict[str, Any] = {
        "modelId": model,
        "messages": _to_converse(msgs),
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature},
    }
    if system:
        req["system"] = [{"text": system}]

    resp = _runtime().converse_stream(**req)
    for event in resp["stream"]:
        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"]["delta"]
            if "text" in delta:
                yield delta["text"]
        elif "metadata" in event:
            u = event["metadata"].get("usage", {})
            track(model, u.get("inputTokens", 0), u.get("outputTokens", 0))


# ── embeddings ──────────────────────────────────────────────────────────────
def embed(
    texts: str | Sequence[str],
    *,
    model: str | None = None,
    dimensions: int = 1024,
) -> list[list[float]]:
    """Titan Text Embeddings V2.

    Titan has no batch endpoint — one call per text. At 2,000 chunks that is
    2,000 calls, which is slow but costs fractions of a cent. Day 3's async
    fan-out pattern applies: use a semaphore, not a for-loop, in real code.

    `dimensions` accepts 256 / 512 / 1024. Smaller vectors cost less to store and
    query and are often barely worse — measure it on Day 14 rather than assuming.
    """
    model = model or settings.bedrock_embed_model
    items = [texts] if isinstance(texts, str) else list(texts)
    rt = _runtime()
    out: list[list[float]] = []
    for t in items:
        body = json.dumps({"inputText": t, "dimensions": dimensions, "normalize": True})
        resp = rt.invoke_model(modelId=model, body=body)
        payload = json.loads(resp["body"].read())
        out.append(payload["embedding"])
        track(model, payload.get("inputTextTokenCount", 0), 0)
    return out


# ── tool use ────────────────────────────────────────────────────────────────
def tool_spec(name: str, description: str, schema: dict) -> dict:
    """Wrap a JSON Schema into Bedrock's toolSpec shape.

    Contrast with Day 7: OpenAI nests under {"type":"function","function":{...}}
    and hands you `arguments` as a JSON *string*. Bedrock nests under
    {"toolSpec":{...,"inputSchema":{"json":...}}} and hands you `input` as a
    parsed *object*. Same concept, three incompatible envelopes across providers —
    which is exactly why fdekit has one seam.
    """
    return {
        "toolSpec": {
            "name": name,
            "description": description,
            "inputSchema": {"json": schema},
        }
    }


def extract_tool_uses(resp: dict) -> list[dict]:
    """Pull [{id, name, input}] out of a Converse response."""
    if resp.get("stopReason") != "tool_use":
        return []
    return [
        {
            "id": b["toolUse"]["toolUseId"],
            "name": b["toolUse"]["name"],
            "input": b["toolUse"]["input"],
        }
        for b in resp["output"]["message"]["content"]
        if "toolUse" in b
    ]


def tool_result_message(tool_use_id: str, content: Any, is_error: bool = False) -> dict:
    """Build the user-role message that returns a tool result to the model."""
    block: dict[str, Any] = {
        "toolUseId": tool_use_id,
        "content": [{"json": content} if isinstance(content, dict) else {"text": str(content)}],
    }
    if is_error:
        block["status"] = "error"
    return {"role": "user", "content": [{"toolResult": block}]}


# ── guardrails ──────────────────────────────────────────────────────────────
def with_guardrail(req: dict, guardrail_id: str, version: str = "DRAFT") -> dict:
    """Attach a Bedrock Guardrail to a Converse request.

    Billing is per policy per 1,000 text units. Four policies enabled means four
    charges on the same call — see AWS_COST_DISCIPLINE.md before looping.
    """
    req["guardrailConfig"] = {
        "guardrailIdentifier": guardrail_id,
        "guardrailVersion": version,
        "trace": "enabled",
    }
    return req
