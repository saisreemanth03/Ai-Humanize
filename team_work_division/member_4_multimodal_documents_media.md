# Member 4: Multimodal Ingestion Pipeline (Documents & Audio/Video)

## 1. Role Title
**Multimodal Data Processing & Ingestion Pipeline Lead**

## 2. Technical Responsibilities
1. **Document Upload & Parsing Service:** Developed `document_extractor.py` handling multi-page PDF ingestion (`PyPDF2`), Word documents (`python-docx`), and raw text files (`.txt`).
2. **Audio/Video Extraction Pipeline:** Created speech-to-text integration utilizing Whisper and FFmpeg to ingest MP3, WAV, MP4, and MOV files.
3. **Safety & Size Validation:** Implemented backend validation guards in `validator.py` verifying file formats, maximum payload size limits (50MB media, 10MB docs), and sanitized byte streams.
4. **Document Studio Interface:** Created `DocumentStudio.jsx` featuring animated drag-and-drop dropzones, file previews, and automatic text extraction into the studio workspace.
5. **Media Studio Interface:** Developed `MediaStudio.jsx` with real-time audio waveform indicators, transcription loading states, and direct transfer into the humanizer pipeline.

---

## 3. Assigned Files to Commit & Push
- `backend/app/services/document_extractor.py`
- `backend/app/services/validator.py`
- `frontend/src/pages/studio/DocumentStudio.jsx`
- `frontend/src/pages/studio/MediaStudio.jsx`

---

## 4. Git Push Commands (To Show on GitHub)

```bash
# 1. Switch to a feature branch
git checkout -b feature/multimodal-ingestion

# 2. Stage assigned files
git add backend/app/services/document_extractor.py
git add backend/app/services/validator.py
git add frontend/src/pages/studio/DocumentStudio.jsx
git add frontend/src/pages/studio/MediaStudio.jsx

# 3. Commit with clear message
git commit -m "feat(multimodal): add document parsing, audio/video transcription, and upload dropzones"

# 4. Push to remote repository
git push -u origin feature/multimodal-ingestion
```
*(Once pushed, open a Pull Request on GitHub to merge into `main`)*
