# Gemini Integration & AI Usage Limit Architecture

## 1. Provider & SDK Integration

The AI pipeline is powered by Google Gemini through the official `google-genai` SDK (`from google import genai`).

- **Configured Model:** `gemini-2.0-flash` (or `gemini-1.5-flash`), configurable via `GEMINI_MODEL` in `.env`.
- **Structured Output:** Enforces strict Pydantic schema validation using `response_schema=LLMShotDesignerOutput` and `response_mime_type="application/json"`.
- **Automatic Recovery:** If Gemini returns JSON that fails Pydantic schema validation, the provider automatically performs **at most one retry**, appending the specific validation error details to the correction prompt.
- **Timeout Management:** All calls are wrapped in `asyncio.wait_for(..., timeout=settings.llm_timeout_seconds)`.
- **Error Mapping:**
  - Upstream 429 quota exhaustion or rate limits -> HTTP 503 (`ai_service_error`)
  - Authentication failure -> HTTP 503 (`ai_service_error`)
  - Timeout -> HTTP 503 (`ai_service_error`)
  - Schema unrecoverable parsing error -> HTTP 502 (`ai_validation_error`)

---

## 2. Anti-Hallucination & Grounding Safeguards

1. **Untrusted User Input Guard:** The system prompt instructs Gemini that the scene description is untrusted creative narrative text and cannot override system instructions or constraints.
2. **Knowledge Base ID Sanitization:** The prompt instructs Gemini to only reference IDs of techniques included in the prompt context. To eliminate hallucinations completely, `services/shot_designer.py` filters all returned `knowledge_base_ids` against the set of UUIDs that were actually retrieved from the database. Any invented UUID is stripped before saving to the database.
3. **Scientific Humility:** Prompts strictly forbid absolute psychological claims (e.g., claiming a low-angle shot "will cause viewers to blame character A"). Recommendations describe context-dependent emotional tendencies, requiring cinematographers to account for performance, lighting, and sound design.

---

## 3. Daily AI Usage Rate Limiting

To prevent accidental quota exhaustion or abuse of the shared Google AI Studio key:

- **Backend Enforcement:** The rate limit is checked in `services/shot_designer.py` before making the network call to Gemini.
- **Configurable Limit:** Set by `DAILY_AI_GENERATION_LIMIT` (default: `20` generations per user per day).
- **UTC Day Boundary:** Evaluated from `00:00:00 UTC` of the current calendar day:
  ```python
  today_utc_start = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)
  ```
- **Failed Call Protection:** Only successful runs that complete database persistence insert a row into `ai_usage`. Failed calls or upstream timeouts are not billed against the user's daily quota.
- **Concurrency Consideration:** In high-concurrency environments, multiple requests from the same user within milliseconds might read the same count before committing. For single-user and standard multi-user filmmaker workloads, standard transaction isolation is sufficient.
