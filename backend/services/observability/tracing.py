"""
Datadog tracing helpers and LLM Observability setup.

Tries to import ddtrace for full LLM Observability.
Falls back to no-op shims if ddtrace is unavailable (e.g. Python 3.13).
"""

import os
import functools
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

_LLMOBS_AVAILABLE = False
_RealLLMObs = None

try:
    from ddtrace.llmobs import LLMObs as _ImportedLLMObs
    _RealLLMObs = _ImportedLLMObs
    _LLMOBS_AVAILABLE = True
    logger.info("ddtrace LLMObs imported successfully")
except Exception:
    logger.info("ddtrace LLMObs not available — using no-op shims")


def init_llm_obs() -> None:
    """Initialize Datadog LLM Observability. Call once at startup."""
    if not _LLMOBS_AVAILABLE:
        logger.info("LLM Observability disabled (ddtrace not available)")
        return
    try:
        dd_api_key = (os.environ.get("DD_API_KEY") or "").strip()
        dd_site = os.environ.get("DD_SITE", "datadoghq.com")
        if not dd_api_key:
            logger.info("LLM Observability disabled (no DD_API_KEY)")
            return
        _RealLLMObs.enable(
            ml_app="aex",
            api_key=dd_api_key,
            site=dd_site,
            env=os.environ.get("DD_ENV", "demo"),
            service=os.environ.get("DD_SERVICE", "aex"),
            agentless_enabled=True,
        )
        logger.info("Datadog LLM Observability enabled (agentless)")
    except Exception as e:
        logger.warning("Failed to enable LLM Observability: %s", e)


class LLMObs:
    """
    Wrapper around ddtrace.llmobs.LLMObs.
    Falls back to no-ops if ddtrace is not available.
    """

    @staticmethod
    @contextmanager
    def llm(model_name: str = "", model_provider: str = "", name: str = ""):
        if _LLMOBS_AVAILABLE and _RealLLMObs:
            try:
                with _RealLLMObs.llm(model_name=model_name, model_provider=model_provider, name=name) as s:
                    yield s
            except Exception as e:
                logger.debug("LLMObs.llm span failed: %s", e)
                yield None
        else:
            yield None

    @staticmethod
    def annotate(span=None, input_data=None, output_data=None, metrics=None):
        if _LLMOBS_AVAILABLE and _RealLLMObs and span is not None:
            try:
                kwargs = {"span": span}
                if input_data is not None:
                    kwargs["input_data"] = input_data
                if output_data is not None:
                    kwargs["output_data"] = output_data
                if metrics is not None:
                    kwargs["metrics"] = metrics
                _RealLLMObs.annotate(**kwargs)
            except Exception as e:
                logger.debug("LLMObs.annotate failed: %s", e)


@contextmanager
def span(name: str, resource: str | None = None, tags: dict | None = None):
    yield None


@contextmanager
def llm_span(model_name: str, agent_label: str):
    with LLMObs.llm(model_name=model_name, model_provider="bedrock", name=agent_label) as s:
        yield s


def trace_fn(name: str, tags: dict | None = None):
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
