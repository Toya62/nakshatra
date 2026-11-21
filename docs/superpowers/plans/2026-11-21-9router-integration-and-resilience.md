# 9router AI Engine Integration and Resilience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate local 9router as the primary AI synthesis gateway for the Nakshatra Vedic Astrology Engine with multi-tier failover, streaming error recovery, resilient timeouts, and direct Gradio & Next.js UI consultation interfaces.

**Architecture:** Connect the stateful RAG pipeline to 9router's OpenAI-compatible endpoint (`http://localhost:20128/v1`) using the pre-configured `nakshatra-combo` model. Introduce a resilient fallback chain: `9router (nakshatra-combo)` → `Google GenAI` (if valid API key) → `Ollama` → `FallbackSynthesizer` (deterministic classical citations). Harden Server-Sent Events (SSE) streaming against transport drops and surface actionable recovery controls in both Next.js and Gradio UIs.

**Tech Stack:** Python 3.11+, FastAPI, OpenAI SDK, Google GenAI SDK, 9router (port 20128), Next.js 16 (App Router), React 19, Gradio.

**Spec:** Nakshatra AI Consultation Specification: 9router primary routing with zero-hang failover.

## Global Constraints

- Never hang indefinitely: every network request to an LLM provider must have a strict timeout (max 15s).
- Fallback guarantee: when 9router or external LLMs are unreachable, consultation must never crash; it must cleanly return classical scriptural citations with clear status notices.
- Streaming integrity: SSE streams (`/rag/ask/stream`) must always yield a terminating `done` or graceful `token` notice without dropping connections unhandled.
- UI resilience: frontend consultation must clear loading spinners on failure, maintain previous chat history, and display actionable recovery buttons.

## Review Focus

1. **Provider Resolution**: `AI_PROVIDER=9router` in `.env` must take precedence over dummy/ambient Google keys.
2. **Offline 9router Handling**: When port 20128 is not running, RAG consultation must fail over smoothly to classical fallback references in < 2 seconds.
3. **Invalid Model Error**: If a model credentials error occurs (e.g. `antigravity inactive`), the synthesizer must catch and attempt combo or fallback models.
4. **SSE Streaming Drop**: If an exception occurs mid-stream, client receives graceful text token indicating service status followed by `done` with citations.
5. **No Regressions**: Existing chart calculation, Ashtakoota, Muhurtha, and bilingual Nepali-English features must remain 100% operational.

---

### Task 1: 9router Provider Priority & Environment Alignment

**Files:**
- Modify: `.env`
- Modify: `nakshatra/ai/service.py:59-94`
- Create: `tests/test_ai_provider_priority.py`

**Interfaces:**
- Consumes: `os.environ["AI_PROVIDER"]`, `os.environ["OPENAI_BASE_URL"]`, `os.environ["OPENAI_MODEL"]`
- Produces: `_default_synthesizer() -> BaseSynthesizer` returning `LLMSynthesizer` configured for 9router when set.

- [x] **Step 1: Write failing unit test for provider priority**

```python
# tests/test_ai_provider_priority.py
import os
import pytest
from nakshatra.ai.service import _default_synthesizer
from nakshatra.ai.synthesize import LLMSynthesizer

def test_9router_priority_over_ambient_google_key(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "9router")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:20128/v1")
    monkeypatch.setenv("OPENAI_MODEL", "nakshatra-combo")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "AQ.dummy-antigravity-token")
    
    synth = _default_synthesizer()
    assert isinstance(synth, LLMSynthesizer)
    assert synth.provider == "openai"
    assert synth.model == "nakshatra-combo"
    assert synth._base_url == "http://localhost:20128/v1"
```

- [x] **Step 2: Run test to confirm failure**

```bash
.venv/bin/pytest tests/test_ai_provider_priority.py
```

- [x] **Step 3: Update `nakshatra/ai/service.py` to give 9router/router explicit first priority**

```python
# nakshatra/ai/service.py
def _default_synthesizer() -> BaseSynthesizer:
    """LLM synthesizer priority: explicit 9router/router -> Google GenAI -> OpenAI -> Ollama -> Fallback."""
    ai_provider = (os.environ.get("AI_PROVIDER") or "").lower().strip()
    google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    openai_base_url = os.environ.get("OPENAI_BASE_URL")

    # Priority 1: 9router / custom OpenAI router
    if (ai_provider in ("9router", "router") or (openai_base_url and ai_provider != "google")) and _module_available("openai"):
        model = os.environ.get("OPENAI_MODEL", "nakshatra-combo")
        api_key = os.environ.get("OPENAI_API_KEY")
        return LLMSynthesizer(provider="openai", model=model, api_key=api_key, base_url=openai_base_url)

    # Priority 2: Direct Google GenAI (only with valid Google AI key, not session tokens)
    is_session_token = bool(google_key and google_key.startswith("AQ."))
    if (ai_provider == "google" or (google_key and not is_session_token and ai_provider not in ("openai", "router", "9router"))) and _module_available("google.genai"):
        if google_key and not is_session_token:
            return LLMSynthesizer(provider="google", model="gemini-3.8-flash", api_key=google_key)

    # Priority 3: Standard OpenAI
    if os.environ.get("OPENAI_API_KEY") and ai_provider != "google" and _module_available("openai"):
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        return LLMSynthesizer(provider="openai", model=model)

    # Priority 4: Ollama local offline
    if (
        os.environ.get("USE_OLLAMA")
        or os.environ.get("OLLAMA_HOST")
        or os.environ.get("OLLAMA_MODEL")
    ) and _module_available("openai"):
        return OllamaSynthesizer(
            model=os.environ.get("OLLAMA_MODEL", "qwen2.5:3b"),
            base_url=os.environ.get("OLLAMA_HOST", "http://localhost:11434/v1"),
        )

    return FallbackSynthesizer()
```

- [x] **Step 4: Update `.env` with 9router configuration**

```bash
AI_PROVIDER=9router
OPENAI_BASE_URL=http://localhost:20128/v1
OPENAI_API_KEY=sk-296733e9c4d8e17e-zk5kkr-bc6339f4
OPENAI_MODEL=nakshatra-combo
```

- [x] **Step 5: Run tests and verify pass**

```bash
.venv/bin/pytest tests/test_ai_provider_priority.py
```

- [x] **Step 6: Commit changes**

```bash
git add .env nakshatra/ai/service.py tests/test_ai_provider_priority.py
git commit -m "fix(ai): prioritize 9router provider and default to nakshatra-combo"
```

---

### Task 2: Resilient Synthesizer Timeouts, Fallback Chain & Stream Fallback

**Files:**
- Modify: `nakshatra/ai/synthesize.py:450-700`
- Create: `tests/test_synthesizer_resilience.py`

**Interfaces:**
- Consumes: `LLMSynthesizer.synthesize`, `LLMSynthesizer.synthesize_stream`
- Produces: Resilient answer generation that never raises uncaught exceptions on provider disconnects.

- [x] **Step 1: Write unit tests for synthesize and synthesize_stream resilience**

```python
# tests/test_synthesizer_resilience.py
import pytest
from nakshatra.ai.retrieval import SearchResult
from nakshatra.ai.corpus import CorpusChunk
from nakshatra.ai.synthesize import LLMSynthesizer

def test_synthesizer_stream_offline_graceful_fallback():
    chunk = CorpusChunk(work="BPHS", chapter="12", verse="5", text="Jupiter in 1st house brings wisdom.")
    results = [SearchResult(chunk=chunk, score=0.9)]
    
    # Point to invalid port to simulate offline 9router
    synth = LLMSynthesizer(provider="openai", model="nakshatra-combo", base_url="http://127.0.0.1:59999/v1", api_key="sk-test")
    
    stream = synth.synthesize_stream("What does Jupiter in 1st house do?", results)
    tokens = list(stream)
    full_output = "".join(tokens)
    
    assert "Notice:" in full_output or "Jupiter in 1st house brings wisdom" in full_output
    assert len(tokens) > 0
```

- [x] **Step 2: Run test to confirm failure**

```bash
.venv/bin/pytest tests/test_synthesizer_resilience.py
```

- [x] **Step 3: Implement timeout and fallback handling in `LLMSynthesizer`**

In `nakshatra/ai/synthesize.py`:
1. In `_complete_google`: configure `Client(http_options={"timeout": 15000})` to prevent hang on dead socket.
2. In `_complete_openai`: catch `openai.APIConnectionError` and `openai.APIError` and attempt fallback.
3. In `synthesize_stream`: wrap generation in try/except. If primary provider fails to stream, yield notice token and fall back to streaming `FallbackSynthesizer` citations token-by-token.

- [x] **Step 4: Run resilience tests and verify pass**

```bash
.venv/bin/pytest tests/test_synthesizer_resilience.py
```

- [x] **Step 5: Commit changes**

```bash
git add nakshatra/ai/synthesize.py tests/test_synthesizer_resilience.py
git commit -m "feat(ai): add 15s timeout and resilient streaming fallback to LLMSynthesizer"
```

---

### Task 3: SSE Endpoint Error Handling in FastAPI

**Files:**
- Modify: `nakshatra/api.py:1432-1510`
- Create: `tests/test_rag_api_stream.py`

**Interfaces:**
- Consumes: `POST /rag/ask/stream`
- Produces: Guaranteed SSE lifecycle emitting `init` → `token`* → `done` without abrupt disconnection.

- [x] **Step 1: Write test for streaming endpoint with simulated offline LLM**

```python
# tests/test_rag_api_stream.py
from fastapi.testclient import TestClient
from nakshatra.api import app

def test_rag_ask_stream_survives_offline_provider():
    client = TestClient(app)
    resp = client.post("/rag/ask/stream", json={"question": "What is the 10th house?", "top_k": 2})
    assert resp.status_code == 200
    assert "data: " in resp.text
    assert '"type": "init"' in resp.text
    assert '"type": "done"' in resp.text or '"type": "token"' in resp.text
```

- [x] **Step 2: Run test to observe behavior**

```bash
.venv/bin/pytest tests/test_rag_api_stream.py
```

- [x] **Step 3: Harden `event_generator()` in `nakshatra/api.py`**

Ensure that if an exception is caught during token streaming, an SSE `token` notice is yielded, followed by a valid `done` payload containing extracted citations from the fallback text, so frontend clients complete cleanly.

- [x] **Step 4: Run test to verify pass**

```bash
.venv/bin/pytest tests/test_rag_api_stream.py
```

- [x] **Step 5: Commit changes**

```bash
git add nakshatra/api.py tests/test_rag_api_stream.py
git commit -m "fix(api): ensure SSE stream completes with done payload on provider errors"
```

---

### Task 4: Next.js Consultation View Error Recovery & Retry UI

**Files:**
- Modify: `web/src/components/ConsultationView.tsx:250-320`

**Interfaces:**
- Consumes: `onError`, `isStreaming`, `error` state
- Produces: Clean message bubble with troubleshooting advice and "Retry Consultation" button.

- [x] **Step 1: Update error handling in `handleSend` in `web/src/components/ConsultationView.tsx`**

1. When `onError` triggers, update the last assistant message:
   - `isStreaming: false`
   - Set text to:
     ```markdown
     ⚠️ **AI Gateway Offline / Connection Error**
     
     Unable to connect to 9router at `http://localhost:20128/v1`.
     - Check if 9router is running: `9router -n -p 20128`
     - Verify active models in 9router (`nakshatra-combo`).
     ```
2. Render an inline "Retry" action button on the message bubble if an error occurred.

- [x] **Step 2: Run TypeScript and build check in `web/`**

```bash
cd web && npm run build
```

- [x] **Step 3: Commit changes**

```bash
git add web/src/components/ConsultationView.tsx
git commit -m "feat(ui): add inline retry button and 9router troubleshooting in consultation view"
```

---

### Task 5: Add AI Consultation Tab to Gradio Entrypoint (`app.py`)

**Files:**
- Modify: `app.py:114-250`
- Create: `tests/test_gradio_consultation.py`

**Interfaces:**
- Consumes: `_rag_service.ask`
- Produces: "AI Jyotish Consultation (RAG + 9router)" tab in Gradio UI.

- [x] **Step 1: Write test for Gradio consultation function**

```python
# tests/test_gradio_consultation.py
from app import consult_rag_ui

def test_consult_rag_ui_returns_text():
    output = consult_rag_ui("What is Jupiter in 1st house?", top_k=2)
    assert isinstance(output, str)
    assert len(output) > 20
```

- [x] **Step 2: Run test to confirm failure**

```bash
.venv/bin/pytest tests/test_gradio_consultation.py
```

- [x] **Step 3: Implement `consult_rag_ui` and Gradio Tab in `app.py`**

Add Gradio tab with question box, optional birth parameters, top_k slider, and Markdown consultation response.

- [x] **Step 4: Run test to verify pass**

```bash
.venv/bin/pytest tests/test_gradio_consultation.py
```

- [x] **Step 5: Commit changes**

```bash
git add app.py tests/test_gradio_consultation.py
git commit -m "feat(hf): add AI Jyotish consultation tab to Gradio app"
```

---

### Task 6: 9router Health Check & Startup Helper Scripts

**Files:**
- Create: `scripts/check_9router.py`
- Create: `scripts/start_9router.sh`

**Interfaces:**
- CLI check utility verifying 9router responsiveness, active providers, and `nakshatra-combo` model availability.

- [x] **Step 1: Create `scripts/check_9router.py`**

Script pings `http://localhost:20128/v1/models`, tests `nakshatra-combo` chat completion, prints clear status report.

- [x] **Step 2: Create `scripts/start_9router.sh`**

Helper script to launch 9router in background with `--skip-update -n -p 20128` if not already running.

- [x] **Step 3: Test scripts**

```bash
.venv/bin/python scripts/check_9router.py
```

- [x] **Step 4: Commit changes**

```bash
git add scripts/check_9router.py scripts/start_9router.sh
git commit -m "chore(scripts): add 9router health check and background startup helper"
```

---

### Verification and Delivery

- [x] Run full test suite: `.venv/bin/pytest tests/`
- [x] Run web build: `cd web && npm run build`
- [x] End-to-end test consultation stream via API
