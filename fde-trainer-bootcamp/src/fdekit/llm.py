"""One chat() function that works against Ollama (free) or OpenAI/Anthropic (paid).

Design note you will re-use on every client engagement: keep ONE seam between your
application and the model provider. Clients change providers mid-project. If every
file in your app imports `openai` directly, that change is a two-week refactor.
Here it is a one-line env var.
"""

from __future__ import annotations

from typing import Any, Iterator, Sequence

from .cost import track
from .settings import settings

Message = dict[str, str]


def _client(backend: str | None = None):
    backend = backend or settings.fdekit_backend

    if backend == "bedrock":
        raise RuntimeError("bedrock is routed in chat()/embed(), not through _client()")

    if backend == "local":
        # Ollama exposes an OpenAI-compatible endpoint. Same SDK, different base_url.
        from openai import OpenAI

        return OpenAI(
            base_url=f"{settings.ollama_base_url}/v1",
            api_key="ollama",  # ignored, but the SDK requires a non-empty string
        )

    if backend == "openai":
        from openai import OpenAI

        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY not set in .env")
        return OpenAI(api_key=settings.openai_api_key)

    if backend == "anthropic":
        from anthropic import Anthropic

        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set in .env")
        return Anthropic(api_key=settings.anthropic_api_key)

    raise ValueError(f"unknown backend: {backend}")


def _normalise(prompt_or_messages: str | Sequence[Message]) -> list[Message]:
    if isinstance(prompt_or_messages, str):
        return [{"role": "user", "content": prompt_or_messages}]
    return list(prompt_or_messages)


def chat(
    prompt_or_messages: str | Sequence[Message],
    *,
    system: str | None = None,
    model: str | None = None,
    backend: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
    **kwargs: Any,
) -> str:
    """Return the assistant's text. Blocking."""
    backend = backend or settings.fdekit_backend

    if backend == "bedrock":
        from . import bedrock as _bedrock

        return _bedrock.chat(
            prompt_or_messages,
            system=system,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    model = model or (
        settings.chat_model if backend == settings.fdekit_backend else None
    )
    messages = _normalise(prompt_or_messages)
    client = _client(backend)

    if backend == "anthropic":
        model = model or settings.anthropic_chat_model
        resp = client.messages.create(
            model=model,
            system=system or "",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        track(model, resp.usage.input_tokens, resp.usage.output_tokens)
        return "".join(b.text for b in resp.content if b.type == "text")

    if system:
        messages = [{"role": "system", "content": system}, *messages]
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )
    if resp.usage:
        track(model, resp.usage.prompt_tokens, resp.usage.completion_tokens)
    return resp.choices[0].message.content or ""


def chat_stream(
    prompt_or_messages: str | Sequence[Message],
    *,
    system: str | None = None,
    model: str | None = None,
    backend: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> Iterator[str]:
    """Yield text chunks as they arrive. Used from Day 15 for streaming APIs."""
    backend = backend or settings.fdekit_backend

    if backend == "bedrock":
        from . import bedrock as _bedrock

        yield from _bedrock.chat_stream(
            prompt_or_messages,
            system=system,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return

    if backend == "anthropic":
        raise NotImplementedError("You implement this on Day 15. That is the lab.")

    model = model or settings.chat_model
    messages = _normalise(prompt_or_messages)
    if system:
        messages = [{"role": "system", "content": system}, *messages]

    stream = _client(backend).chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def embed(
    texts: str | Sequence[str],
    *,
    model: str | None = None,
    backend: str | None = None,
) -> list[list[float]]:
    """Return one vector per input string."""
    backend = backend or settings.fdekit_backend

    if backend == "bedrock":
        from . import bedrock as _bedrock

        return _bedrock.embed(texts, model=model)

    if backend == "anthropic":
        backend = "local"  # Anthropic has no embedding endpoint; fall back
    model = model or settings.embed_model
    items = [texts] if isinstance(texts, str) else list(texts)
    resp = _client(backend).embeddings.create(model=model, input=items)
    return [d.embedding for d in resp.data]
