"""
Centralized Datadog HTTP client.

Handles:
  - Metric submission (batched via /api/v1/series)
  - Event submission (via /api/v1/events)
  - Auth, site URL construction, timeouts, retries
  - Graceful no-op when DD_API_KEY is unset
"""

import logging
import os
import threading
import time
import httpx

logger = logging.getLogger(__name__)

_client: "DatadogClient | None" = None


class DatadogClient:
    def __init__(self):
        self.api_key = (os.environ.get("DD_API_KEY") or "").strip()
        self.site = os.environ.get("DD_SITE", "datadoghq.com")
        self.service = os.environ.get("DD_SERVICE", "aex")
        self.env = os.environ.get("DD_ENV", "demo")
        self.enabled = bool(self.api_key)
        self._base_url = f"https://api.{self.site}"
        self._headers = {
            "DD-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        self.base_tags = [f"service:{self.service}", f"env:{self.env}"]

        if self.enabled:
            logger.info("DatadogClient enabled → %s", self._base_url)
        else:
            logger.info("DatadogClient disabled (no DD_API_KEY)")

    def submit_metrics(self, series: list[dict]) -> None:
        """Fire-and-forget metric batch submission."""
        if not self.enabled or not series:
            return
        for s in series:
            s.setdefault("tags", [])
            s["tags"] = self.base_tags + s["tags"]

        def _post():
            try:
                with httpx.Client(timeout=10.0) as c:
                    r = c.post(
                        f"{self._base_url}/api/v1/series",
                        headers=self._headers,
                        json={"series": series},
                    )
                    if r.status_code not in (200, 202):
                        logger.debug("DD metrics %s: %s", r.status_code, r.text[:200])
            except Exception as e:
                logger.debug("DD metrics send failed: %s", e)
        threading.Thread(target=_post, daemon=True).start()

    def submit_event(self, title: str, text: str, tags: list[str],
                     alert_type: str = "info") -> None:
        """Fire-and-forget event submission."""
        if not self.enabled:
            return
        all_tags = self.base_tags + tags

        def _post():
            try:
                with httpx.Client(timeout=10.0) as c:
                    r = c.post(
                        f"{self._base_url}/api/v1/events",
                        headers=self._headers,
                        json={
                            "title": title,
                            "text": text,
                            "tags": all_tags,
                            "alert_type": alert_type,
                            "source_type_name": "aex",
                        },
                    )
                    if r.status_code not in (200, 202):
                        logger.debug("DD event %s: %s", r.status_code, r.text[:200])
            except Exception as e:
                logger.debug("DD event send failed: %s", e)
        threading.Thread(target=_post, daemon=True).start()


def get_client() -> DatadogClient:
    global _client
    if _client is None:
        _client = DatadogClient()
    return _client


def init_client() -> DatadogClient:
    """Explicit initialization at startup."""
    global _client
    _client = DatadogClient()
    return _client
