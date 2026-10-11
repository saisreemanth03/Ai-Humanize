# Member 5: YouTube Transcript Engine, API Gateway & DevOps

## 1. Role Title
**Backend API Gateway, YouTube Extraction & DevOps Lead**

## 2. Technical Responsibilities
1. **Multi-Strategy YouTube Ingestion:** Implemented `media_extractor.py` featuring a resilient 4-stage pipeline:
   - Supadata cloud managed residential proxy (bypasses datacenter bot blocks).
   - Direct `youtube_transcript_api` scraper with rotating User-Agents.
   - Timedtext XML client parsing.
   - Verbatim subtitle tag cleaner (strips `[music]`, `[applause]`, `>>`, and timestamp offsets).
2. **FastAPI Gateway & Schemas:** Designed API routing in `main.py` and strict Pydantic payload models in `schemas.py` (`/api/humanize`, `/api/extract/youtube`, `/api/extract/document`, `/api/extract/media`).
3. **Frontend API Integration:** Authored `frontend/src/services/api.js` with unified axios/fetch handling, error propagation, and response caching.
4. **YouTube Studio View:** Implemented `YouTubeStudio.jsx` with quick sample links, URL validation, and automated one-click ingestion.
5. **DevOps & Cloud Deployment:** Configured production deployment files (`vercel.json` for frontend edge routing, Render web service for Python backend, CORS origins, and environment variable management).

---

## 3. Assigned Files to Commit & Push
- `backend/app/services/media_extractor.py`
- `backend/app/main.py`
- `backend/app/schemas.py`
- `frontend/src/pages/studio/YouTubeStudio.jsx`
- `frontend/src/services/api.js`
- `vercel.json`

---

## 4. Git Push Commands (To Show on GitHub)

```bash
# 1. Switch to a feature branch
git checkout -b feature/youtube-api-devops

# 2. Stage assigned files
git add backend/app/services/media_extractor.py
git add backend/app/main.py
git add backend/app/schemas.py
git add frontend/src/pages/studio/YouTubeStudio.jsx
git add frontend/src/services/api.js
git add vercel.json

# 3. Commit with clear message
git commit -m "feat(api-devops): build YouTube extraction engine, FastAPI gateway, and Vercel cloud deployment"

# 4. Push to remote repository
git push -u origin feature/youtube-api-devops
```
*(Once pushed, open a Pull Request on GitHub to merge into `main`)*
