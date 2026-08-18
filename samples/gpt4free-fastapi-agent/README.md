# gpt4free FastAPI sample

A small, self-contained FastAPI server that exposes an OpenAI-compatible
`/v1/chat/completions`, `/v1/responses`, and `/v1/models` API backed by
[gpt4free (g4f)](https://github.com/xtekky/gpt4free). It's meant as a
minimal reference you can point Codex CLI, or any other code agent /
tool that speaks the OpenAI API, at.

**No API key required.** By default this sample uses g4f's `Pollinations`
provider (model `openai-fast`), which is free and needs no account, key,
or login — it just works out of the box.

> This sample is unrelated to llama.cpp's core inference engine — it lives
> here only as a self-contained example and does not build or run as part
> of the C++ project. `gpt4free` proxies third-party providers with no SLA
> or reliability guarantees; use at your own risk and respect each
> provider's terms of service.

## What's here

- `main.py` — the FastAPI app
- `requirements.txt`
- `.env.example` — optional configuration

Unlike gpt4free's own bundled server (`g4f api`), this sample only
implements chat completions, the Responses API, and model listing, so
it's easy to read end-to-end and extend. Both `/v1/chat/completions` and
`/v1/responses` are backed by the same free, no-auth provider — they're
just two different request/response shapes over the same underlying
completion.

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
    "model": "openai-fast",
    "messages": [{"role": "user", "content": "Say hello in one word"}]
  }'
```

No `Authorization` header is needed unless you set `SAMPLE_API_KEY`.

Streaming works the same way OpenAI's API does — pass `"stream": true` and
read the `data: ...` Server-Sent-Events lines.

Or, using the Responses API shape (what Codex CLI sends):

```bash
curl http://localhost:8000/v1/responses \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o", "input": "Say hello in one word"}'
```

## Using it with a code agent (Codex CLI, etc.)

Most OpenAI-API-compatible CLI agents let you override the API base URL
and key via environment variables. Point them at this server instead of
`api.openai.com`:

```bash
export OPENAI_BASE_URL=http://localhost:8000/v1
export OPENAI_API_KEY=anything   # most CLIs require this var to be non-empty, but the value is ignored unless you set SAMPLE_API_KEY
```

Then run your agent as usual (e.g. `codex`, or any tool that reads
`OPENAI_BASE_URL`/`OPENAI_API_KEY`). Check your agent's docs for the exact
variable names it expects — some use `OPENAI_API_BASE` instead.

### Codex CLI specifically

Codex CLI talks to custom providers via `~/.codex/config.toml`, and its
`wire_api` setting picks which request/response shape it sends — `"chat"`
for `/v1/chat/completions`, or `"responses"` for `/v1/responses`. This
sample implements both, so either works; here's the `"responses"` form:

```toml
model = "gpt-4o"
model_provider = "my_custom_proxy"

[model_providers.my_custom_proxy]
name = "Custom AI Proxy Gateway"
base_url = "http://localhost:8000/v1"
wire_api = "responses"
```

Notes:
- Leave out `env_key` entirely — with no `env_key`, Codex sends no
  `Authorization` header, which matches this server's default (auth
  disabled). If you set `SAMPLE_API_KEY`, add `env_key = "OPENAI_API_KEY"`
  here and export that variable before running `codex`.
- `model = "gpt-4o"` is just a label Codex sends along with the request;
  this server ignores it and always answers from `DEFAULT_MODEL`/
  `DEFAULT_PROVIDER` (see `.env.example`). It is **not** real GPT-4o —
  see "Why not real chatgpt.com?" below for why.
- If you deploy this server somewhere other than your machine, change
  `base_url` to that address (must end in `/v1`) — e.g.
  `https://your-own-domain.example/v1`. Only point it at a host you
  control and trust; anyone who can reach that URL can read/inject into
  your Codex sessions.
- `/v1/responses` here covers plain text messages (streaming and
  non-streaming) — no tool calls, reasoning items, or file/image inputs.
  If Codex sends those, this server will just ignore the extra fields.

## Why not real chatgpt.com?

g4f can also drive the actual chatgpt.com web UI (provider `OpenaiChat`),
which avoids OpenAI's paid API but is *not* auth-free in practice: chatgpt.com
sits behind Cloudflare, so g4f needs either a HAR file exported from a
logged-in browser session or automated browser login (`nodriver`), and it
still breaks whenever OpenAI changes their anti-bot checks. `Pollinations`
was picked as the default instead because it needs zero setup and just
works. If you want to try `OpenaiChat` anyway, set
`DEFAULT_PROVIDER=OpenaiChat` and see g4f's README for HAR-file/cookie
setup (the "har_and_cookies" directory):
https://github.com/xtekky/gpt4free#readme

## Notes / limitations

- No tool/function-calling, vision, or image endpoints — only text chat.
- Model availability depends entirely on which upstream providers gpt4free
  can currently reach; `GET /v1/models` lists what g4f believes is
  available right now, across all providers (not just the no-auth default).
- Authentication is a single shared bearer token (`SAMPLE_API_KEY`),
  suitable for local development only — do not expose this server to the
  public internet as-is. It's disabled by default, and is unrelated to
  whether the upstream provider (Pollinations) needs a key — it doesn't.
