# Hosting the API

Easiest options: **Railway** or **Render**. Both give you a public URL (e.g. `https://your-app.up.railway.app` or `https://your-app.onrender.com`) and set `PORT` for you.

---

## Option A: Railway

1. Push your code to **GitHub** (if not already).
2. Go to [railway.app](https://railway.app) → Sign in with GitHub.
3. **New Project** → **Deploy from GitHub repo** → select `sinehanllm`.
4. Railway will detect the app. If it doesn’t pick a start command, set:
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Variables** (Settings → Variables): add every env var from your `.env`:
   - `GEMINI_API_KEY`
   - `GEMINI_MODEL_NAME` (optional, default `gemini-2.5-flash`)
   - `GEMINI_MAX_OUTPUT_TOKENS` (optional, default `8192`)
   - `QDRANT_URL`
   - `QDRANT_API_KEY`
   - `EMBEDDING_MODEL_NAME`
   - `EMBEDDING_DIMENSION` (optional, default `384`)
6. Deploy. Use the generated URL (e.g. `https://xxx.up.railway.app`) as your API base in Netlify env.

---

## Option B: Render

1. Push your code to **GitHub**.
2. Go to [render.com](https://render.com) → Sign in → **New** → **Web Service**.
3. Connect your repo `sinehanllm`.
4. **Build & deploy:**
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Environment** (Environment tab): add the same variables as above.
6. Create Web Service. Use the URL (e.g. `https://your-app.onrender.com`) in Netlify env.

---

## Env vars to set on the host

| Variable | Required | Example |
|----------|----------|---------|
| `GEMINI_API_KEY` | Yes | your Gemini API key |
| `QDRANT_URL` | Yes | your Qdrant Cloud URL |
| `QDRANT_API_KEY` | Yes | your Qdrant API key |
| `EMBEDDING_MODEL_NAME` | Yes | e.g. `BAAI/bge-small-en-v1.5` |
| `GEMINI_MODEL_NAME` | No | `gemini-2.5-flash` (default) |
| `GEMINI_MAX_OUTPUT_TOKENS` | No | `8192` (default) |
| `EMBEDDING_DIMENSION` | No | `384` (default) |

---

## After deploy

- Set your Netlify env (e.g. `VITE_API_URL`) to the hosted API URL, e.g. `https://your-app.up.railway.app` (no trailing slash).
- Redeploy the Netlify site so the frontend uses the new API URL.
