"""
MiniMax Text-to-Speech integration.
Called after Bedrock analysis to generate a voice summary.
See docs/MINIMAX_SPEC.md for full spec.
"""

import os
import re
import logging
import httpx

logger = logging.getLogger(__name__)

MINIMAX_TTS_URL = "https://api.minimax.chat/v1/t2a_v2"
MINIMAX_ENABLED = os.environ.get("MINIMAX_ENABLED", "false").lower() == "true"


def is_enabled() -> bool:
    return MINIMAX_ENABLED and bool(os.environ.get("MINIMAX_API_KEY"))


def prepare_text(text: str) -> str:
    """Clean and truncate analysis text for TTS."""
    # Remove markdown formatting
    clean = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    clean = re.sub(r"#{1,6}\s", "", clean)
    clean = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", clean)
    clean = re.sub(r"\n+", " ", clean).strip()
    # Prepend and truncate
    prefix = "AEX Market Update. "
    suffix = " This concludes the simulated market summary."
    body = clean[:480]
    return f"{prefix}{body}{suffix}"


async def synthesize(text: str) -> str | None:
    """
    Call MiniMax TTS API.
    Returns base64-encoded audio data URI, or None if unavailable.
    """
    if not is_enabled():
        logger.info("MiniMax TTS disabled or unconfigured")
        return None

    api_key   = os.environ["MINIMAX_API_KEY"]
    group_id  = os.environ.get("MINIMAX_GROUP_ID", "")

    clean_text = prepare_text(text)

    payload = {
        "model": "speech-01-turbo",
        "text": clean_text,
        "voice_setting": {
            "voice_id": "male-qn-qingse",
            "speed": 1.0,
            "vol": 1.0,
            "pitch": 0,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
        },
    }

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(
                MINIMAX_TTS_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                params={"GroupId": group_id} if group_id else {},
            )
            resp.raise_for_status()
            data = resp.json()

            # MiniMax returns audio in data.audio_file (base64) or a URL
            audio_data = data.get("data", {})
            if "audio_file" in audio_data:
                return f"data:audio/mp3;base64,{audio_data['audio_file']}"
            if "audio_url" in audio_data:
                return audio_data["audio_url"]

            logger.warning(f"MiniMax unexpected response shape: {data.keys()}")
            return None

    except httpx.TimeoutException:
        logger.warning("MiniMax TTS timed out")
        return None
    except Exception as e:
        logger.error(f"MiniMax TTS error: {e}")
        return None
