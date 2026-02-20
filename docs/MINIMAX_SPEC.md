# MiniMax Integration Specification

## Purpose

MiniMax provides ONE "wow factor" feature: a **voice market summary**. After the Bedrock Market Analyst produces a text analysis, MiniMax converts it to a spoken audio summary. This is demo polish, not core functionality.

## When It's Called

```
User clicks "Run Analysis"
    │
    ▼
Bedrock Market Analyst produces text analysis
    │
    ▼
Text is displayed in the CopilotKit chat panel
    │
    ▼
"Play Audio Summary" button appears
    │
    ▼
User clicks → text sent to MiniMax TTS → audio plays in browser
```

MiniMax is ONLY called:
- After Bedrock analysis completes
- When user explicitly clicks "Play Audio Summary"
- Never automatically, never for core logic

## API Integration

### MiniMax Text-to-Speech API

**Endpoint**: `https://api.minimax.chat/v1/t2a_v2`

**Request**:
```json
{
  "model": "speech-01-turbo",
  "text": "<market analysis text, max 500 chars>",
  "voice_setting": {
    "voice_id": "male-qn-qingse",
    "speed": 1.0,
    "vol": 1.0,
    "pitch": 0
  },
  "audio_setting": {
    "sample_rate": 32000,
    "bitrate": 128000,
    "format": "mp3"
  }
}
```

**Headers**:
```
Authorization: Bearer <MINIMAX_API_KEY>
Content-Type: application/json
```

**Response**: JSON with base64-encoded audio data or audio URL.

### Input Preparation

Before sending to MiniMax, truncate and clean the analysis text:
1. Take the first 500 characters of the Bedrock analysis
2. Remove markdown formatting (**, ##, etc.)
3. Remove any JSON or code blocks
4. Prepend: "AEX Market Update. "
5. Append: "This concludes the simulated market summary."

### Output Handling

1. Decode base64 audio (or fetch audio URL)
2. Play in browser via Web Audio API or `<audio>` element
3. Show a small audio player widget with play/pause

## Backend Endpoint

```
POST /audio/summary
Body: { "text": "analysis text here" }
Response: { "audio_url": "data:audio/mp3;base64,..." }
```

The backend:
1. Receives text
2. Calls MiniMax TTS API
3. Returns audio data to frontend
4. Emits Datadog span: `minimax.tts` with duration and text length

## Fallback If MiniMax Unavailable

MiniMax is optional. If it fails:

1. **API key not set**: Hide the "Play Audio Summary" button entirely
2. **API returns error**: Show toast "Voice summary unavailable" and do nothing
3. **API timeout (>10s)**: Cancel and show "Voice summary timed out"
4. **Rate limited**: Show "Voice summary temporarily unavailable"

The text analysis is always available regardless of MiniMax status.

## Environment Variables

```
MINIMAX_API_KEY=<key>          # If empty, feature is disabled
MINIMAX_GROUP_ID=<group_id>    # Required by MiniMax API
MINIMAX_ENABLED=true|false     # Kill switch
```

## Demo Script for MiniMax

1. After running Bedrock analysis, say: "And for an extra touch, we can hear the market summary"
2. Click "Play Audio Summary"
3. Audio plays: "AEX Market Update. The regulation shock caused Compliance sector agents to surge..."
4. Takes ~3 seconds to generate, ~10 seconds to play
5. If it fails, say: "Voice is optional — the text analysis is what matters"

## Cost / Rate Limits

- MiniMax free tier: limited requests
- Each call ~500 chars of audio, costs minimal
- We only call it on explicit user action, so 2-3 calls per demo max
