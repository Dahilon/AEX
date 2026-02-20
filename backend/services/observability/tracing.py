"""
Datadog tracing helpers and LLM Observability setup.

ddtrace auto-instruments FastAPI when launched with:
    ddtrace-run uvicorn services.api.main:app

Use span() for manual spans on internal operations.
Use llm_span() to wrap Bedrock calls for LLM Obs.
"""

import os
import functools
import logging
from contextlib import contextmanager
from ddtrace import tracer
from ddtrace.llmobs import LLMObs

logger = logging.getLogger(__name__)


def init_llm_obs() -> None:
    """Initialize Datadog LLM Observability. Call once at startup."""
    LLMObs.enable(
        ml_app="aex",
        api_key=os.environ.get("DD_API_KEY", ""),
        site=os.environ.get("DD_SITE", "datadoghq.com"),
    )
    logger.info("LLM Observability initialized")


@contextmanager
def span(name: str, resource: str | None = None, tags: dict | None = None):
    """Context manager for a custom ddtrace span."""
    with tracer.trace(name, service="aex", resource=resource or name) as s:
        if tags:
            for k, v in tags.items():
                s.set_tag(k, v)
        yield s


@contextmanager
def llm_span(model_name: str, agent_label: str):
    """
    Context manager that wraps a Bedrock call with LLM Observability.

    Usage:
        with llm_span("anthropic.claude-3-5-sonnet", "market_analyst") as span:
            response = bedrock.converse(...)
            LLMObs.annotate(
                span=span,
                input_data=[...],
                output_data=[...],
                metrics={"input_tokens": N, "output_tokens": M}
            )
    """
    with LLMObs.llm(
        model_name=model_name,
        model_provider="bedrock",
        name=agent_label,
    ) as s:
        yield s


def trace_fn(name: str, tags: dict | None = None):
    """Decorator: wrap a function in a ddtrace span."""
    def decorator(fn):
        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            with span(name, tags=tags):
                return await fn(*args, **kwargs)

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            with span(name, tags=tags):
                return fn(*args, **kwargs)

        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(fn) else sync_wrapper
    return decorator
