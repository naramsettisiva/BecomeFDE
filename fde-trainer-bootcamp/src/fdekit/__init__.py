"""fdekit — the shared toolkit you build up over 24 days.

Day 1  : settings, chat()
Day 3  : embed(), cosine_similarity()
Day 4  : chunkers, SimpleVectorStore
Day 5  : eval harness
Day 7  : tool registry, agent loop
Day 13 : LLM-as-judge
Day 15 : caching, guardrails

AWS lane: `bedrock` and `s3vectors` are imported lazily so the core lane runs
with no boto3 and no AWS account. Set FDEKIT_BACKEND=bedrock and every lab from
Day 1 onward runs on AWS with no other change — that is the Day 1 seam paying off.

Import as:  from fdekit import chat, settings
"""

from .settings import settings  # noqa: F401
from .llm import chat, chat_stream, embed  # noqa: F401
from .cost import CostTracker, track  # noqa: F401

__all__ = ["settings", "chat", "chat_stream", "embed", "CostTracker", "track"]
__version__ = "0.1.0"
