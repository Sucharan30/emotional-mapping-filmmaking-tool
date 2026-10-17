# Known Limitations & Next Steps

## 1. What Is Completed in Backend Part 1

- Full PostgreSQL schema migrations (`001`, `002`, `003`, `004`).
- Supabase Email OTP token verification and `/api/v1/auth/me`.
- Multi-tenant data isolation and ownership enforcement for Projects and Scenes.
- Cinematography Knowledge Base library APIs with category, emotion, and review status filtering.
- Google Gemini LLM integration with structured JSON outputs, timeout handling, and auto-retry.
- Shot Designer recommendation generation with anti-hallucination sanitization and atomic rollback.
- Backend daily AI usage rate limiting (20 runs/day per user, resetting 00:00 UTC).
- Uniform `{ "error": { "code": "...", "message": "..." } }` error contract.
- Complete automated unit test suite with fakes/mocks in `backend/tests/`.

---

## 2. What Remains Out of Scope (Future Slices)

The following areas are intentionally scheduled for future development slices:
- **Frontend Application:** React + Vite UI pages, Supabase OTP login form, Shot Designer visual cards.
- **Video Processing Pipeline:** Video upload to Supabase Storage, thumbnail extraction, Gemini multimodal video analysis.
- **Audience Lens:** Persona definition endpoints, AI audience response predictions (`audience_feedback` table).
- **Psychology Experiment:** Survey endpoints, participant code generation, empirical vs AI prediction comparison (`experiment_responses` table).

---

## 3. Known Limitations

1. **In-Memory Auth Token Cache:**
   - Token verifications are cached in memory for 60 seconds.
   - If running across multiple Render containers/dynos, each worker maintains its own short-lived 60s cache. This is safe and performant, but revocation propagation across different containers may take up to 60 seconds.
2. **AI Rate Limiting Concurrency:**
   - Evaluated by querying the `ai_usage` table. Under intense simultaneous requests from the same user account, race conditions could permit a slight overrun of the limit before transactions commit. If distributed atomic locks are needed later, Redis can be introduced.
3. **Database Connection IPv6:**
   - Direct PostgreSQL connections (`port 5432`) may fail on IPv4 cloud hosts. The backend must always use the **Transaction Pooler (port 6543)**.

---

## 4. Next Steps for Frontend Connection

1. The frontend should initialize `supabase-js` using `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`.
2. After the user verifies their email OTP via `supabase.auth.verifyOtp`, grab the `session.access_token`.
3. Configure Axios / Fetch interceptors to attach `Authorization: Bearer ${accessToken}` to every request to the FastAPI backend.
4. Call `GET /api/v1/auth/me` on app load to confirm authentication.
5. Populate dropdowns from `GET /api/v1/meta/options`.
