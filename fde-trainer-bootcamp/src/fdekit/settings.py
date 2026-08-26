"""Central configuration. One place that knows about keys, models, and paths.

Why this exists on Day 1: every FDE engagement starts with someone's half-broken
config. Having a single typed settings object is the difference between "it works
on my machine" and a system you can hand to a client.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- backend selection -------------------------------------------------
    fdekit_backend: Literal["local", "openai", "anthropic", "bedrock"] = "local"

    # --- providers ---------------------------------------------------------
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # --- aws ---------------------------------------------------------------
    aws_profile: str = "fde"
    aws_region: str = "us-east-1"
    bedrock_chat_model: str = "amazon.nova-lite-v1:0"
    bedrock_judge_model: str = "anthropic.claude-sonnet-4-5-20250929-v1:0"
    bedrock_embed_model: str = "amazon.titan-embed-text-v2:0"
    s3_vector_bucket: str | None = None

    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.1:8b"
    ollama_embed_model: str = "nomic-embed-text"

    openai_chat_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-small"
    anthropic_chat_model: str = "claude-sonnet-4-5"

    # --- observability -----------------------------------------------------
    langchain_tracing_v2: bool = False
    langchain_api_key: str | None = None
    langchain_project: str = "fde-bootcamp"

    # --- misc --------------------------------------------------------------
    tavily_api_key: str | None = None
    hf_token: str | None = None
    bootcamp_budget_usd: float = 100.0

    # --- paths -------------------------------------------------------------
    @property
    def root(self) -> Path:
        return ROOT

    @property
    def corpus_dir(self) -> Path:
        p = ROOT / "data" / "corpus"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def index_dir(self) -> Path:
        p = ROOT / "data" / "index"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def evals_dir(self) -> Path:
        p = ROOT / "evals"
        p.mkdir(parents=True, exist_ok=True)
        return p

    # --- derived -----------------------------------------------------------
    @property
    def chat_model(self) -> str:
        return {
            "local": self.ollama_chat_model,
            "openai": self.openai_chat_model,
            "anthropic": self.anthropic_chat_model,
            "bedrock": self.bedrock_chat_model,
        }[self.fdekit_backend]

    @property
    def embed_model(self) -> str:
        return {
            "local": self.ollama_embed_model,
            "openai": self.openai_embed_model,
            "anthropic": self.openai_embed_model,  # no Anthropic embed endpoint
            "bedrock": self.bedrock_embed_model,
        }[self.fdekit_backend]


settings = Settings()
