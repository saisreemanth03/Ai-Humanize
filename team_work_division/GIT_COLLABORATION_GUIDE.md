# Git Collaboration Guide for 5-Member Team

This guide explains how all 5 teammates can collaborate on a single central GitHub repository and have their contributions clearly attributed to their own GitHub accounts when presenting to your project evaluator/sir.

---

## Step 1: Add Teammates as Collaborators on GitHub
The repository owner (main account) should:
1. Go to the repository on GitHub (`https://github.com/saisreemanth03/Ai-Humanize`).
2. Click **Settings** → **Collaborators** → **Add people**.
3. Enter each of the other 4 teammates' GitHub usernames or email addresses.
4. Each teammate accepts the invitation from their email or at `https://github.com/saisreemanth03/Ai-Humanize/invitations`.

---

## Step 2: Teammates Set Up Their Local Machine
Each teammate must configure their own GitHub username and email in Git on their computer so commits show up with their name/avatar:

```bash
git config --global user.name "Teammate Name"
git config --global user.email "teammate_github_email@example.com"
```

---

## Step 3: Clone the Repository
Each teammate runs:
```bash
git clone https://github.com/saisreemanth03/Ai-Humanize.git
cd Ai-Humanize
```

---

## Step 4: Work on Assigned Feature Branches
To keep the history clean and demonstrate individual contributions:

### Member 1:
```bash
git checkout -b feature/core-ai-engine
# Work on assigned files: backend/app/services/humanizer.py, ai_client.py, prompts.py, heuristic_humanizer.py, entity_checks.py
git add backend/app/services/humanizer.py backend/app/services/ai_client.py backend/app/prompts.py backend/app/utils/heuristic_humanizer.py backend/app/utils/entity_checks.py
git commit -m "feat(ai-engine): implement dual-pass humanizer, LLM client fallback, and entity guardrails"
git push -u origin feature/core-ai-engine
```

### Member 2:
```bash
git checkout -b feature/frontend-design-system
# Work on assigned files: Navbar.jsx, Footer.jsx, StudioLayout.jsx, App.jsx, App.css, index.css, Home.jsx
git add frontend/src/components/Navbar.jsx frontend/src/components/Footer.jsx frontend/src/layouts/StudioLayout.jsx frontend/src/App.jsx frontend/src/App.css frontend/src/index.css frontend/src/pages/Home.jsx
git commit -m "feat(ui): build responsive mobile navigation, studio segmented control, and WCAG AA design system"
git push -u origin feature/frontend-design-system
```

### Member 3:
```bash
git checkout -b feature/studio-diff-inspection
# Work on assigned files: StudioWorkspace.jsx, InspectionDrawer.jsx, diffHelper.js, constants.js, TextStudio.jsx
git add frontend/src/components/StudioWorkspace.jsx frontend/src/components/InspectionDrawer.jsx frontend/src/utils/diffHelper.js frontend/src/utils/constants.js frontend/src/pages/studio/TextStudio.jsx
git commit -m "feat(studio): implement dual-pane workspace, visual word diff engine, and inspection drawer"
git push -u origin feature/studio-diff-inspection
```

### Member 4:
```bash
git checkout -b feature/multimodal-ingestion
# Work on assigned files: document_extractor.py, validator.py, DocumentStudio.jsx, MediaStudio.jsx
git add backend/app/services/document_extractor.py backend/app/services/validator.py frontend/src/pages/studio/DocumentStudio.jsx frontend/src/pages/studio/MediaStudio.jsx
git commit -m "feat(multimodal): add document parsing, audio/video transcription, and upload dropzones"
git push -u origin feature/multimodal-ingestion
```

### Member 5:
```bash
git checkout -b feature/youtube-api-devops
# Work on assigned files: media_extractor.py, main.py, schemas.py, YouTubeStudio.jsx, api.js, vercel.json
git add backend/app/services/media_extractor.py backend/app/main.py backend/app/schemas.py frontend/src/pages/studio/YouTubeStudio.jsx frontend/src/services/api.js vercel.json
git commit -m "feat(api-devops): build YouTube extraction engine, FastAPI gateway, and Vercel cloud deployment"
git push -u origin feature/youtube-api-devops
```

---

## Step 5: Merge via Pull Requests on GitHub
1. Once each branch is pushed, navigate to the GitHub repository.
2. Click **Compare & pull request** for each branch.
3. Review the code diffs and click **Merge pull request** → **Confirm merge**.
4. Now, if you go to **Insights → Contributors** on GitHub:
   - All **5 team members** will be shown with their exact commit counts, lines added, and files modified!
   - Under the **Network graph** and **Branches**, your sir will clearly see each member's individual branch and work stream.
