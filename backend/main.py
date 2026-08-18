import os
import base64
import hashlib
import requests

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
NETLIFY_AUTH_TOKEN = os.getenv("NETLIFY_AUTH_TOKEN")


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="VibeBuilder AI",
    description="AI Website Generator Backend",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "https://vibebuil.netlify.app",
        "https://www.vibebuil.netlify.app",

        # Local development
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# OPENROUTER CLIENT
# ============================================================

if not OPENROUTER_API_KEY:
    print("WARNING: OPENROUTER_API_KEY is not set")

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)


# ============================================================
# REQUEST MODELS
# ============================================================

class GenerateRequest(BaseModel):
    prompt: str


class EditRequest(BaseModel):
    html: str
    instruction: str


class PublishRequest(BaseModel):
    html: str


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "VibeBuilder AI backend is running",
        "status": "ok"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# ============================================================
# GENERATE WEBSITE
# ============================================================

@app.post("/generate")
def generate_website(request: GenerateRequest):

    if not request.prompt.strip():
        raise HTTPException(
            status_code=400,
            detail="Prompt cannot be empty"
        )

    if not OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OPENROUTER_API_KEY is not configured on the server"
        )

    system_prompt = """
You are VibeBuilder AI, an expert web developer.

Create a complete single-page website from the user's request.

Return ONLY the complete HTML document.

Requirements:

- HTML5
- Responsive design
- Modern polished UI
- CSS inside <style>
- JavaScript inside <script> when needed
- Use realistic content
- Use reliable external image URLs when images are needed
- Do not use Markdown
- Do not explain anything
- Return only valid HTML
- Start with <!DOCTYPE html>
- End with </html>
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b:free",

            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": request.prompt
                }
            ],

            temperature=0.7
        )

        html = response.choices[0].message.content

        if not html:
            raise HTTPException(
                status_code=500,
                detail="AI returned empty response"
            )

        # Remove Markdown code fences if AI accidentally adds them
        html = html.strip()

        if html.startswith("```html"):
            html = html[7:]

        elif html.startswith("```"):
            html = html[3:]

        if html.endswith("```"):
            html = html[:-3]

        html = html.strip()

        return {
            "success": True,
            "html": html
        }

    except Exception as e:

        print("GENERATION ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=f"AI generation failed: {str(e)}"
        )


# ============================================================
# EDIT WEBSITE
# ============================================================

@app.post("/edit")
def edit_website(request: EditRequest):

    if not request.html.strip():
        raise HTTPException(
            status_code=400,
            detail="HTML cannot be empty"
        )

    if not request.instruction.strip():
        raise HTTPException(
            status_code=400,
            detail="Edit instruction cannot be empty"
        )

    if not OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OPENROUTER_API_KEY is not configured"
        )

    system_prompt = """
You are VibeBuilder AI.

You are editing an existing HTML website.

Return ONLY the complete modified HTML document.

Rules:

- Preserve existing functionality unless the user asks to change it.
- Apply the user's requested changes.
- Keep the website responsive.
- Keep CSS inside <style>.
- Keep JavaScript inside <script>.
- Do not use Markdown.
- Do not explain anything.
- Return only valid HTML.
- Start with <!DOCTYPE html>.
- End with </html>.
"""

    user_prompt = f"""
Here is the existing website:

{request.html}

User's requested change:

{request.instruction}

Return the complete updated HTML.
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b:free",

            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],

            temperature=0.7
        )

        html = response.choices[0].message.content

        if not html:
            raise HTTPException(
                status_code=500,
                detail="AI returned empty response"
            )

        html = html.strip()

        if html.startswith("```html"):
            html = html[7:]

        elif html.startswith("```"):
            html = html[3:]

        if html.endswith("```"):
            html = html[:-3]

        html = html.strip()

        return {
            "success": True,
            "html": html
        }

    except Exception as e:

        print("EDIT ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=f"AI editing failed: {str(e)}"
        )


# ============================================================
# PUBLISH TO NETLIFY
# ============================================================

@app.post("/publish")
def publish_website(request: PublishRequest):

    if not request.html.strip():
        raise HTTPException(
            status_code=400,
            detail="HTML cannot be empty"
        )

    if not NETLIFY_AUTH_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="NETLIFY_AUTH_TOKEN is not configured on the server"
        )

    try:

        # ----------------------------------------------------
        # Create a Netlify site
        # ----------------------------------------------------

        headers = {
            "Authorization": f"Bearer {NETLIFY_AUTH_TOKEN}",
            "Content-Type": "application/json"
        }

        create_site_response = requests.post(
            "https://api.netlify.com/api/v1/sites",
            headers=headers,
            json={}
        )

        if create_site_response.status_code not in [200, 201]:
            print(
                "NETLIFY CREATE ERROR:",
                create_site_response.status_code,
                create_site_response.text
            )

            raise HTTPException(
                status_code=500,
                detail=f"Netlify API error: {create_site_response.text}"
            )

        site = create_site_response.json()

        site_id = site.get("id")
        site_url = site.get("ssl_url") or site.get("url")

        if not site_id:
            raise HTTPException(
                status_code=500,
                detail="Netlify did not return a site ID"
            )

        # ----------------------------------------------------
        # Prepare index.html
        # ----------------------------------------------------

        file_content = request.html.encode("utf-8")

        file_hash = hashlib.sha1(file_content).hexdigest()

        files_payload = {
            "index.html": file_hash
        }

        # ----------------------------------------------------
        # Create deploy
        # ----------------------------------------------------

        deploy_response = requests.post(
            f"https://api.netlify.com/api/v1/sites/{site_id}/deploys",
            headers=headers,
            json={
                "files": files_payload
            }
        )

        if deploy_response.status_code not in [200, 201]:
            print(
                "NETLIFY DEPLOY ERROR:",
                deploy_response.status_code,
                deploy_response.text
            )

            raise HTTPException(
                status_code=500,
                detail=f"Netlify deploy error: {deploy_response.text}"
            )

        deploy = deploy_response.json()

        deploy_id = deploy.get("id")

        # ----------------------------------------------------
        # Upload index.html
        # ----------------------------------------------------

        upload_headers = {
            "Authorization": f"Bearer {NETLIFY_AUTH_TOKEN}",
            "Content-Type": "application/octet-stream"
        }

        upload_response = requests.put(
            f"https://api.netlify.com/api/v1/deploys/{deploy_id}/files/index.html",
            headers=upload_headers,
            data=file_content
        )

        if upload_response.status_code not in [200, 201]:
            print(
                "NETLIFY UPLOAD ERROR:",
                upload_response.status_code,
                upload_response.text
            )

            raise HTTPException(
                status_code=500,
                detail=f"Netlify upload error: {upload_response.text}"
            )

        return {
            "success": True,
            "url": site_url,
            "site_id": site_id,
            "deploy_id": deploy_id
        }

    except HTTPException:
        raise

    except Exception as e:

        print("PUBLISH ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=f"Publishing failed: {str(e)}"
        )