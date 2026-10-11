# Member 1: Core AI Humanization Engine & LLM Orchestrator

## 1. Role Title
**Team Lead & Core AI Engine Specialist**

## 2. Technical Responsibilities
1. **Dual-Pass LLM Orchestration:** Developed the core humanizer service (`humanizer.py`) that executes generation pass 1 (natural human phrasing) followed by pass 2 (strict entity and tone verification).
2. **Multi-Model Client Fallbacks:** Implemented Groq (`llama-3.3-70b-versatile`) with automatic fallback to Google Gemini (`gemini-1.5-flash`) in `ai_client.py`.
3. **Domain Prompt Engineering:** Built domain-tailored system prompts for Academic, Executive, Creative, Technical, and Journalistic writing in `prompts.py`.
4. **Heuristic Offline Humanizer:** Designed the rule-based local rewrite engine in `heuristic_humanizer.py` ensuring service reliability when API keys are unconfigured or offline.
5. **Entity Protection Guardrails:** Implemented regex entity matchers in `entity_checks.py` to preserve numbers, URLs, dates, and proper nouns.

---

## 3. Assigned Files to Commit & Push
- `backend/app/services/humanizer.py`
- `backend/app/services/ai_client.py`
- `backend/app/prompts.py`
- `backend/app/utils/heuristic_humanizer.py`
- `backend/app/utils/entity_checks.py`

---

## 4. Git Push Commands (To Show on GitHub)

```bash
# 1. Switch to a feature branch
git checkout -b feature/core-ai-engine

# 2. Stage assigned files
git add backend/app/services/humanizer.py
git add backend/app/services/ai_client.py
git add backend/app/prompts.py
git add backend/app/utils/heuristic_humanizer.py
git add backend/app/utils/entity_checks.py

# 3. Commit with clear message
git commit -m "feat(ai-engine): implement dual-pass humanizer, LLM client fallback, and entity guardrails"

# 4. Push to remote repository
git push -u origin feature/core-ai-engine
```
*(Once pushed, open a Pull Request on GitHub to merge into `main`)*
