# Step-by-Step Manual Verification Guide

This guide is designed for you to test and verify the entire backend locally on your computer.  
**No commands or network requests were executed automatically.** Follow each step below in sequence.

---

## Step 0: Prerequisites & SQL Reconciliation

If you have already executed migrations `001`, `002`, and `003` in your Supabase SQL Editor:
1. Open the Supabase Dashboard -> **SQL Editor** -> **New query**.
2. Open `backend/sql/004_schema_reconciliation.sql` in your editor.
3. Copy the entire file content, paste it into the Supabase SQL editor, and click **Run**.
4. **Why run this?** It adds performance indexes for foreign keys (`user_id`, `project_id`, `scene_id`, `category`, and `potential_emotions`) and creates the `updated_at` trigger without touching or deleting any existing tables or rows.
5. **Read-only verification query:**
   ```sql
   SELECT indexname, tablename FROM pg_indexes 
   WHERE schemaname = 'public' 
     AND indexname IN ('idx_projects_user_id', 'idx_scenes_project_id', 'idx_shot_recommendations_scene_id');
   ```
   *Success:* Returns 3 rows showing the new indexes on `projects`, `scenes`, and `shot_recommendations`.

---

## Step 1: Open Terminal & Activate Virtual Environment

1. Open PowerShell or Command Prompt on your computer.
2. Change directory to the project root:
   ```powershell
   cd "d:\CreatED\Emotional Mapping Film Making tool"
   ```
3. Verify Python version (Python 3.10, 3.11, or 3.12 recommended):
   ```powershell
   python --version
   ```
4. Activate your existing virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   *(If on standard CMD: `venv\Scripts\activate.bat`)*  
   *Success:* Your terminal prompt will show `(venv)` at the beginning of the line.

---

## Step 2: Install / Update Dependencies

Run the following command from the project root:
```powershell
pip install -r backend/requirements.txt
```
*Success:* All packages (`fastapi`, `uvicorn`, `pydantic-settings`, `sqlalchemy`, `asyncpg`, `supabase`, `httpx`, `google-genai`, `pytest`, `pytest-asyncio`, `aiosqlite`) finish installing without build errors.

---

## Step 3: Configure `.env` File

1. Ensure you have a `.env` file at the project root (`d:\CreatED\Emotional Mapping Film Making tool\.env`).
2. If starting fresh, copy `.env.example`:
   ```powershell
   Copy-Item .env.example .env
   ```
3. Open `.env` in your editor and verify these exact settings:
   - `DATABASE_URL`: Ensure you are using the **Transaction Pooler** (port `6543`), not the direct connection (port `5432`):
     ```env
     DATABASE_URL=postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
     ```
   - `SUPABASE_URL`: e.g. `https://xyzproject.supabase.co`
   - `SUPABASE_ANON_KEY`: Your Supabase anon public key
   - `GEMINI_API_KEY`: Your key from Google AI Studio (`https://aistudio.google.com/`)
   - `GEMINI_MODEL`: `gemini-2.0-flash`
   - `LLM_PROVIDER`: `gemini`
   - `LLM_THINKING_LEVEL`: `none`
   - `ALLOWED_ORIGINS`: `http://localhost:5173`
   - `DAILY_AI_GENERATION_LIMIT`: `20`

---

## Step 4: Run the Automated Unit Test Suite

Run the tests (using mocked external services — safe, fast, no live API credits used):
```powershell
cd backend
pytest -v
```
*What it checks:*
- Auth verification and token expiry handling.
- Project & Scene CRUD and cross-user ownership isolation.
- Knowledge base listing, category/emotion filtering, and error codes.
- Shot Designer structured output, schema retries, rate limits, and rollback.
- API validation errors, health checks, and CORS headers.

*Success:* All test suites pass with green checkmarks.

---

## Step 5: Start the Backend Server Locally

From the `backend` directory with `(venv)` active:
```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
*Success:* The terminal displays:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```
*If it fails to start:*
- If error mentions `database_url`: Check that `DATABASE_URL` is set in `.env` and port `6543` is specified.
- If error mentions `GEMINI_API_KEY`: Check that the key is in `.env`.

---

## Step 6: Verify in Browser & Swagger UI

1. Open your web browser and navigate to:
   [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)  
   *Success:* Displays `{"status":"ok","environment":"development","version":"1.0.0"}`

2. Open the interactive API documentation:
   [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
   *Success:* The Swagger UI opens showing all endpoints under `/api/v1/...` (`/auth`, `/meta`, `/projects`, `/scenes`, `/knowledge-base`).

3. Test Metadata Options:
   In Swagger UI, expand `GET /api/v1/meta/options` -> Click **Try it out** -> **Execute**.  
   *Success:* Returns HTTP 200 with all controlled lists of emotions, budgets, and complexity levels.

---

## Step 7: How to Obtain a Valid Supabase Auth Token for Testing

To test protected endpoints, you need an access token from Supabase:

### Method A (Via Supabase Dashboard - Easiest & Safest)
1. In your Supabase Dashboard, go to **Authentication** -> **Users**.
2. If you don't have a user yet, click **Add User** -> **Create User** (enter an email and password).
3. Open your browser console (F12) or use a temporary PowerShell script to sign in and get your token:
   Run in a separate PowerShell window:
   ```powershell
   $body = @{
       email = "your-email@example.com"
       password = "your-password"
   } | ConvertTo-Json

   $res = Invoke-RestMethod -Method Post -Uri "https://[YOUR-PROJECT-ID].supabase.co/auth/v1/token?grant_type=password" `
       -Headers @{ "apikey" = "YOUR-SUPABASE-ANON-KEY" } `
       -ContentType "application/json" `
       -Body $body

   $token = $res.access_token
   Write-Host "Bearer Token:"
   Write-Host $token
   ```
4. Copy the output `$token`.

### Method B (Authorize in Swagger UI)
1. On `http://127.0.0.1:8000/docs`, click the **Authorize** green button at the top right.
2. In the `HTTPBearer` value box, paste your `$token`.
3. Click **Authorize** -> **Close**.  
   Now all subsequent requests in Swagger UI will automatically include `Authorization: Bearer <token>`.

---

## Step 8: Verify End-to-End API Workflows in Swagger UI

### 1. Test `/api/v1/auth/me`
- Expand `GET /api/v1/auth/me` -> Click **Execute**.
- *Success:* Returns HTTP 200 with your user UUID and email.

### 2. Test Knowledge Base
- Expand `GET /api/v1/knowledge-base`.
- Enter `category`: `angle`.
- Click **Execute**.
- *Success:* Returns HTTP 200 with entries like "Low Angle", "High Angle", "Dutch Angle".

### 3. Create a Project
- Expand `POST /api/v1/projects`.
- Enter body:
  ```json
  {
    "name": "Cinematic Test Project",
    "type": "shot_design",
    "description": "Validating the Shot Designer workflow."
  }
  ```
- Click **Execute**.
- *Success:* Returns HTTP 201 with project `id`. Copy this `id`.

### 4. Create a Scene
- Expand `POST /api/v1/scenes`.
- Enter body (replace `project_id` with your copied ID):
  ```json
  {
    "project_id": "YOUR-PROJECT-ID",
    "description": "An exhausted marathon runner collapses on the track in front of an empty stadium.",
    "target_emotion": "vulnerability",
    "character_focus": "character_a",
    "production_budget": "low",
    "budget_notes": "Outdoor track in natural overcast daylight."
  }
  ```
- Click **Execute**.
- *Success:* Returns HTTP 201 with scene `id`. Copy this `scene_id`.

### 5. Generate Shot Designer Recommendations (Live Gemini Call!)
- Expand `POST /api/v1/scenes/design-shots`.
- Enter body:
  ```json
  {
    "scene_id": "YOUR-SCENE-ID"
  }
  ```
- Click **Execute**.
- *What happens:*
  - Backend verifies your token and ownership.
  - Checks you haven't exceeded 20 calls today.
  - Queries knowledge base techniques matching "vulnerability".
  - Calls Gemini (`gemini-2.0-flash`) with structured output enforcement.
  - Saves 4–5 recommendations atomically to Supabase PostgreSQL.
  - Logs token usage in `ai_usage`.
- *Success:* Returns HTTP 200 with 4–5 recommendations, visual checklists, and `model_used: "gemini-2.0-flash"`.

### 6. Retrieve Saved Recommendations
- Expand `GET /api/v1/scenes/{scene_id}/recommendations`.
- Click **Execute**.
- *Success:* Returns HTTP 200 with the saved recommendations from PostgreSQL.

---

## Step 9: Common Errors & Troubleshooting

| Error | Root Cause | Solution |
|---|---|---|
| `401 missing_token` | No Bearer token sent | Click "Authorize" in Swagger UI and supply your token. |
| `401 invalid_token` | Token expired or invalid project ref | Re-generate token or verify `SUPABASE_URL` / `SUPABASE_ANON_KEY`. |
| `404 project_not_found` | Project was created under a different user ID | Ensure the user logged in matches the project's `user_id`. |
| `429 daily_limit_exceeded` | You reached 20 generations today | Reset count in `ai_usage` or increase `DAILY_AI_GENERATION_LIMIT` in `.env`. |
| `502 ai_validation_error` | Gemini output failed Pydantic schema validation | Gemini retried once and failed; re-run with clearer scene description. |
| `503 ai_service_error` | Gemini API key invalid or rate-limited | Check `GEMINI_API_KEY` in Google AI Studio. |
| `password authentication failed` | Incorrect password in `DATABASE_URL` | Check your Supabase database password in `.env`. |
