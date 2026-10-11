# HumanizeAI — 5-Member Team Project Division & Work Matrix

## Executive Summary (For Evaluation & Project Review)
**Project Title:** HumanizeAI — Multimodal Natural Prose Refinement & Entity-Preserving Writing Studio  
**Target Goal:** Transform AI-generated and machine-drafted content into natural, human-flowing prose while strictly verifying factual entities, numbers, dates, and domain terminology.  
**Tech Stack:** React 18 (Vite), Vanilla CSS Design System, FastAPI (Python), Groq / Google Gemini LLM API, YouTube Transcript Multi-Client Engine, Whisper & PyPDF2/docx.

---

## Team Division Overview

| Member # | Assigned Role | Primary Focus Area | Core Technologies | Key Deliverable Files |
| :--- | :--- | :--- | :--- | :--- |
| **Member 1** | **Team Lead & Core AI Engine Specialist** | LLM Orchestration, Dual-Pass Prompts, Entity Verification & Heuristics | Python, Groq, Gemini API, Regex Heuristics | `backend/app/services/humanizer.py`<br>`backend/app/services/ai_client.py`<br>`backend/app/prompts.py`<br>`backend/app/utils/heuristic_humanizer.py`<br>`backend/app/utils/entity_checks.py` |
| **Member 2** | **Frontend Architect & UI/UX Specialist** | Responsive Navigation, Mobile Studio Segmented Control, Design System & WCAG AA Contrast | React, React Router, Vanilla CSS, Lucide Icons | `frontend/src/components/Navbar.jsx`<br>`frontend/src/components/Footer.jsx`<br>`frontend/src/layouts/StudioLayout.jsx`<br>`frontend/src/App.jsx`<br>`frontend/src/App.css`<br>`frontend/src/index.css`<br>`frontend/src/pages/Home.jsx` |
| **Member 3** | **Interactive Studio & Client Analytics Lead** | Dual-Pane Editor, Myers Word Diffing Engine, Instant Cliché & Robotic Score Detector | React, JS String Algorithms, LCS Diffs, Analytics | `frontend/src/components/StudioWorkspace.jsx`<br>`frontend/src/components/InspectionDrawer.jsx`<br>`frontend/src/utils/diffHelper.js`<br>`frontend/src/utils/constants.js`<br>`frontend/src/pages/studio/TextStudio.jsx` |
| **Member 4** | **Multimodal Ingestion & Document Processing Lead** | File Upload Handling (PDF, DOCX, TXT), Audio/Video Speech Ingestion & Validation Guardrails | Python (PyPDF2, python-docx), React Drag-Drop, Audio/Video Parsing | `backend/app/services/document_extractor.py`<br>`backend/app/services/validator.py`<br>`frontend/src/pages/studio/DocumentStudio.jsx`<br>`frontend/src/pages/studio/MediaStudio.jsx` |
| **Member 5** | **API Gateway, YouTube Pipeline & DevOps Lead** | YouTube Subtitle Extraction, Proxy Fallback, FastAPI Endpoints, Vercel & Render Deployment | FastAPI, Pydantic, Supadata Proxy, Vercel, Render CI/CD | `backend/app/services/media_extractor.py`<br>`backend/app/main.py`<br>`backend/app/schemas.py`<br>`frontend/src/pages/studio/YouTubeStudio.jsx`<br>`frontend/src/services/api.js`<br>`vercel.json` |

---

## Collaboration Architecture

```
                                 [SHARED GITHUB REPOSITORY]
                                             │
      ┌──────────────────┬───────────────────┼───────────────────┬──────────────────┐
      ▼                  ▼                   ▼                   ▼                  ▼
[Member 1 Branch]  [Member 2 Branch]   [Member 3 Branch]   [Member 4 Branch]  [Member 5 Branch]
feature/ai-engine  feature/ui-nav      feature/diff-studio feature/multimodal feature/api-devops
      │                  │                   │                   │                  │
      └──────────────────┴───────────────────┴───────────────────┴──────────────────┘
                                             │
                                     (Merge to `main`)
                                             ▼
                               [Production CI/CD Deploy]
                               Vercel (UI) + Render (API)
```

---

## Detailed Member Assignment Files in this Directory
1. `member_1_ai_engine.md` — Detailed responsibilities, file list, and Git commands for Member 1.
2. `member_2_frontend_design_system.md` — Detailed responsibilities, file list, and Git commands for Member 2.
3. `member_3_studio_diff_inspection.md` — Detailed responsibilities, file list, and Git commands for Member 3.
4. `member_4_multimodal_documents_media.md` — Detailed responsibilities, file list, and Git commands for Member 4.
5. `member_5_youtube_api_devops.md` — Detailed responsibilities, file list, and Git commands for Member 5.
6. `GIT_COLLABORATION_GUIDE.md` — Complete tutorial for team members to collaborate on GitHub.
