# Member 3: Dual-Pane Writing Studio, Word Diffing & Client Analytics

## 1. Role Title
**Interactive Studio Engineer & Client-Side Analytics Specialist**

## 2. Technical Responsibilities
1. **Dual-Pane Writing Workspace:** Built the responsive synchronized dual-pane editor in `StudioWorkspace.jsx` with input cleaning strips and independent scroll containers.
2. **Myers Word-Level Visual Diffing:** Engineered the client-side diff algorithm in `diffHelper.js` using Longest Common Subsequence (LCS) to highlight added humanized phrasing in green and replaced robotic wording in red.
3. **Instant Cliché & Robotic Score Detector:** Implemented real-time heuristics in `constants.js` to scan for buzzwords (*delve*, *testament*, *tapestry*, *furthermore*) and compute instant readability scores before submitting to the backend.
4. **Inspection & Validation Drawer:** Built `InspectionDrawer.jsx` to render detailed entity audit summaries, tone checks, sentence burstiness metrics, and entity preservation badges.
5. **Text Studio Page:** Connected the main text humanization route in `TextStudio.jsx` with keyboard shortcuts, copy-to-clipboard, and text file export.

---

## 3. Assigned Files to Commit & Push
- `frontend/src/components/StudioWorkspace.jsx`
- `frontend/src/components/InspectionDrawer.jsx`
- `frontend/src/utils/diffHelper.js`
- `frontend/src/utils/constants.js`
- `frontend/src/pages/studio/TextStudio.jsx`

---

## 4. Git Push Commands (To Show on GitHub)

```bash
# 1. Switch to a feature branch
git checkout -b feature/studio-diff-inspection

# 2. Stage assigned files
git add frontend/src/components/StudioWorkspace.jsx
git add frontend/src/components/InspectionDrawer.jsx
git add frontend/src/utils/diffHelper.js
git add frontend/src/utils/constants.js
git add frontend/src/pages/studio/TextStudio.jsx

# 3. Commit with clear message
git commit -m "feat(studio): implement dual-pane workspace, visual word diff engine, and inspection drawer"

# 4. Push to remote repository
git push -u origin feature/studio-diff-inspection
```
*(Once pushed, open a Pull Request on GitHub to merge into `main`)*
