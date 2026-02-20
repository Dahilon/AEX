"""
Datadog tracing helpers and LLM Observability setup.

ddtrace auto-instruments FastAPI when launched with:
    ddtrace-run uvicorn services.api.main:app

Use span() for manual spans on internal operations.
Use llm_span() to wrap Bedrock calls for LLM Obs.

NOTE: ddtrace disabled due to Python 3.13 compatibility issues.
These functions are stubbed out.
"""

import os
import functools
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


def init_llm_obs() -> None:
    """Initialize Datadog LLM Observability. Call once at startup."""
    logger.info("LLM Observability disabled (ddtrace not available)")


@contextmanager
def span(name: str, resource: str | None = None, tags: dict | None = None):
    """Context manager for a custom ddtrace span (disabled)."""
    yield None


@contextmanager
def llm_span(model_name: str, agent_label: str):
    """
    Context manager that wraps a Bedrock call with LLM Observability (disabled).

    Usage:
        with llm_span("anthropic.claude-3-5-sonnet", "market_analyst") as span:
            response = bedrock.converse(...)
    """
    yield None


def trace_fn(name: str, tags: dict | None = None):
    """Decorator: wrap a function in a ddtrace span (disabled)."""
    def decorator(fn):
        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            return await fn(*args, **kwargs)

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(fn) else sync_wrapper
    return decorator
