# gpt4free FastAPI sample

A small, self-contained FastAPI server that exposes an OpenAI-compatible
`/v1/chat/completions` and `/v1/models` API backed by
[gpt4free (g4f)](https://github.com/xtekky/gpt4free). It's meant as a
minimal reference you can point Codex CLI, or any other code agent /
tool that speaks the OpenAI API, at.

> This sample is unrelated to llama.cpp's core inference engine — it lives
> here only as a self-contained example and does not build or run as part
> of the C++ project. `gpt4free` proxies third-party providers with no SLA
> or reliability guarantees; use at your own risk and respect each
> provider's terms of service.

## What's here

- `main.py` — the FastAPI app (~130 lines)
- `requirements.txt`
- `.env.example` — optional configuration

Unlike gpt4free's own bundled server (`g4f api`), this sample only
implements chat completions and model listing, so it's easy to read
end-to-end and extend.

## Setup

```bash
cd samples/gpt4free-fastapi-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
# or: uvicorn main:app --reload --port 8000
```

The server listens on `http://localhost:8000` by default (override with
`PORT`). Optional settings (`SAMPLE_API_KEY`, `DEFAULT_MODEL`,
`DEFAULT_PROVIDER`) are documented in `.env.example` — export them before
starting the server, e.g.:

```bash
export SAMPLE_API_KEY=local-dev-key
python main.py
```

## Try it

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Say hello in one word"}]
  }'
```

Streaming works the same way OpenAI's API does — pass `"stream": true` and
read the `data: ...` Server-Sent-Events lines.

## Using it with a code agent (Codex CLI, etc.)

Most OpenAI-API-compatible CLI agents let you override the API base URL
and key via environment variables. Point them at this server instead of
`api.openai.com`:

```bash
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=local-dev-key   # must match SAMPLE_API_KEY if you set one, else any value
```

Then run your agent as usual (e.g. `codex`, or any tool that reads
`OPENAI_BASE_URL`/`OPENAI_API_KEY`). Check your agent's docs for the exact
variable names it expects — some use `OPENAI_API_BASE` instead.

## Notes / limitations

- No tool/function-calling, vision, or image endpoints — only text chat.
- Model availability depends entirely on which upstream providers gpt4free
  can currently reach; `GET /v1/models` lists what g4f believes is
  available right now.
- Authentication is a single shared bearer token (`SAMPLE_API_KEY`),
  suitable for local development only — do not expose this server to the
  public internet as-is.
