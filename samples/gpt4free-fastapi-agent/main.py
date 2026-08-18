"""
Minimal OpenAI-compatible FastAPI server backed by gpt4free (g4f).

This exposes just enough of the OpenAI Chat Completions API for
code agents such as Codex CLI, Aider, Continue, etc. to talk to it:

    GET  /v1/models
    POST /v1/chat/completions   (streaming and non-streaming)

Point any OpenAI-API-compatible client at this server by setting:

    OPENAI_BASE_URL=http://localhost:8000/v1
    OPENAI_API_KEY=<SAMPLE_API_KEY below, or anything if auth is disabled>

See README.md in this directory for setup and usage details.
"""

from __future__ import annotations

import json
import os
from typing import List, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from g4f.client import AsyncClient
from g4f.errors import (
    MissingAuthError,
    ModelNotFoundError,
    ProviderNotFoundError,
    RateLimitError,
)
from g4f.providers.any_provider import AnyProvider

# Optional bearer token required from callers. Leave unset to disable auth
# (fine for local use, e.g. on localhost only).
SAMPLE_API_KEY = os.getenv("SAMPLE_API_KEY")

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER") or None

app = FastAPI(title="gpt4free FastAPI sample", version="0.1.0")
client = AsyncClient()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = DEFAULT_MODEL
    messages: List[ChatMessage]
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    provider: Optional[str] = DEFAULT_PROVIDER


def check_auth(authorization: Optional[str]) -> None:
    if SAMPLE_API_KEY is None:
        return
    token = (authorization or "").removeprefix("Bearer ").strip()
    if token != SAMPLE_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/v1/models")
async def list_models(authorization: Optional[str] = Header(None)):
    check_auth(authorization)
    models = AnyProvider.get_models()
    return {
        "object": "list",
        "data": [
            {"id": model, "object": "model", "created": 0, "owned_by": "g4f"}
            for model in models
        ],
    }


@app.post("/v1/chat/completions")
async def chat_completions(
    body: ChatCompletionRequest, authorization: Optional[str] = Header(None)
):
    check_auth(authorization)

    kwargs = {
        "model": body.model,
        "messages": [m.model_dump() for m in body.messages],
        "stream": body.stream,
    }
    if body.provider:
        kwargs["provider"] = body.provider
    if body.temperature is not None:
        kwargs["temperature"] = body.temperature
    if body.max_tokens is not None:
        kwargs["max_tokens"] = body.max_tokens

    try:
        response = client.chat.completions.create(**kwargs)

        if not body.stream:
            result = await response
            return json.loads(result.model_dump_json())

        async def event_stream():
            try:
                async for chunk in response:
                    payload = (
                        chunk.model_dump_json()
                        if hasattr(chunk, "model_dump_json")
                        else chunk.json()
                    )
                    yield f"data: {payload}\n\n"
            except (RateLimitError, MissingAuthError) as e:
                yield f"data: {json.dumps({'error': {'message': str(e)}})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except (ModelNotFoundError, ProviderNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except MissingAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        # g4f providers fail often (rate limits, auth walls, outages).
        # Surface the underlying reason instead of a bare 500.
        raise HTTPException(status_code=502, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
