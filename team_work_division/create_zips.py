import os
import zipfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "team_work_division", "member_zips")

os.makedirs(OUTPUT_DIR, exist_ok=True)

MEMBERS = {
    "member_1_ai_engine.zip": {
        "title": "Member 1: Core AI Humanization Engine & LLM Orchestrator",
        "branch": "feature/core-ai-engine",
        "commit_msg": "feat(ai-engine): implement dual-pass humanizer, LLM client fallback, and entity guardrails",
        "files": [
            "backend/app/services/humanizer.py",
            "backend/app/services/ai_client.py",
            "backend/app/prompts.py",
            "backend/app/utils/heuristic_humanizer.py",
            "backend/app/utils/entity_checks.py",
        ]
    },
    "member_2_frontend_design_system.zip": {
        "title": "Member 2: Frontend Architecture, Navigation & Design System",
        "branch": "feature/frontend-design-system",
        "commit_msg": "feat(ui): build responsive mobile navigation, studio segmented control, and WCAG AA design system",
        "files": [
            "frontend/src/components/Navbar.jsx",
            "frontend/src/components/Footer.jsx",
            "frontend/src/layouts/StudioLayout.jsx",
            "frontend/src/App.jsx",
            "frontend/src/App.css",
            "frontend/src/index.css",
            "frontend/src/pages/Home.jsx",
        ]
    },
    "member_3_studio_diff_inspection.zip": {
        "title": "Member 3: Dual-Pane Writing Studio, Word Diffing & Client Analytics",
        "branch": "feature/studio-diff-inspection",
        "commit_msg": "feat(studio): implement dual-pane workspace, visual word diff engine, and inspection drawer",
        "files": [
            "frontend/src/components/StudioWorkspace.jsx",
            "frontend/src/components/InspectionDrawer.jsx",
            "frontend/src/utils/diffHelper.js",
            "frontend/src/utils/constants.js",
            "frontend/src/pages/studio/TextStudio.jsx",
        ]
    },
    "member_4_multimodal_documents_media.zip": {
        "title": "Member 4: Multimodal Ingestion Pipeline (Documents & Audio/Video)",
        "branch": "feature/multimodal-ingestion",
        "commit_msg": "feat(multimodal): add document parsing, audio/video transcription, and upload dropzones",
        "files": [
            "backend/app/services/document_extractor.py",
            "backend/app/services/validator.py",
            "frontend/src/pages/studio/DocumentStudio.jsx",
            "frontend/src/pages/studio/MediaStudio.jsx",
        ]
    },
    "member_5_youtube_api_devops.zip": {
        "title": "Member 5: YouTube Transcript Engine, API Gateway & DevOps",
        "branch": "feature/youtube-api-devops",
        "commit_msg": "feat(api-devops): build YouTube extraction engine, FastAPI gateway, and Vercel cloud deployment",
        "files": [
            "backend/app/services/media_extractor.py",
            "backend/app/main.py",
            "backend/app/schemas.py",
            "frontend/src/pages/studio/YouTubeStudio.jsx",
            "frontend/src/services/api.js",
            "vercel.json",
        ]
    }
}

for zip_filename, data in MEMBERS.items():
    zip_path = os.path.join(OUTPUT_DIR, zip_filename)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write instruction text file
        instructions = f"""======================================================================
{data['title']}
======================================================================

HOW TO PUSH THESE FILES TO GITHUB:
1. Clone the project repository if not already cloned:
   git clone https://github.com/saisreemanth03/Ai-Humanize.git
   cd Ai-Humanize

2. Set your personal GitHub author name and email:
   git config user.name "Your Name"
   git config user.email "your_github_email@example.com"

3. Create and switch to your feature branch:
   git checkout -b {data['branch']}

4. Copy the files in this zip into your local repository root folder.
   (The subfolder structure backend/... and frontend/... matches perfectly!)

5. Stage your assigned files:
"""
        for rel_file in data['files']:
            instructions += f"   git add {rel_file}\n"

        instructions += f"""
6. Commit your changes:
   git commit -m "{data['commit_msg']}"

7. Push to the shared GitHub repository:
   git push -u origin {data['branch']}

8. Go to GitHub, click 'Compare & pull request', and merge into main!
======================================================================
"""
        zf.writestr("INSTRUCTIONS_TO_PUSH.txt", instructions)

        # Add each assigned file preserving directory structure
        for rel_file in data["files"]:
            abs_file = os.path.join(BASE_DIR, rel_file)
            if os.path.exists(abs_file):
                zf.write(abs_file, arcname=rel_file)
                print(f"[{zip_filename}] Added: {rel_file}")
            else:
                print(f"[{zip_filename}] WARNING: Not found: {abs_file}")

    print(f"Successfully generated: {zip_path}\n")

print("All 5 member zip packages created successfully.")
