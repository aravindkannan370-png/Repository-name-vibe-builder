import os
import io
import json
import hashlib
import secrets
import urllib.request
import urllib.error

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI


# --------------------------------------------------
# Load environment variables
# --------------------------------------------------

load_dotenv()

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
netlify_token = os.getenv("NETLIFY_AUTH_TOKEN")

if not openrouter_api_key:
    raise RuntimeError(
        "OPENROUTER_API_KEY is missing from .env"
    )

if not netlify_token:
    raise RuntimeError(
        "NETLIFY_AUTH_TOKEN is missing from .env"
    )


# --------------------------------------------------
# OpenRouter client
# --------------------------------------------------

client = OpenAI(
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1",
)


# --------------------------------------------------
# FastAPI
# --------------------------------------------------

app = FastAPI(title="VibeBuilder AI")


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Request models
# --------------------------------------------------

class GenerateRequest(BaseModel):
    prompt: str


class EditRequest(BaseModel):
    html: str
    instruction: str


class PublishRequest(BaseModel):
    html: str


# --------------------------------------------------
# Root
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "VibeBuilder AI backend is running"
    }


# --------------------------------------------------
# Health
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# ==================================================
# GENERATE
# ==================================================

@app.post("/generate")
def generate_website(request: GenerateRequest):

    if not request.prompt.strip():
        raise HTTPException(
            status_code=400,
            detail="Prompt cannot be empty"
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
            max_tokens=5000,
        )

        website = response.choices[0].message.content

        if not website:
            raise Exception(
                "AI returned empty HTML."
            )

        website = website.strip()

        if website.startswith("```html"):
            website = website[7:]

        elif website.startswith("```"):
            website = website[3:]

        if website.endswith("```"):
            website = website[:-3]

        website = website.strip()

        return {
            "success": True,
            "html": website
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==================================================
# EDIT
# ==================================================

@app.post("/edit")
def edit_website(request: EditRequest):

    if not request.html.strip():
        raise HTTPException(
            status_code=400,
            detail="Website HTML cannot be empty"
        )

    if not request.instruction.strip():
        raise HTTPException(
            status_code=400,
            detail="Edit instruction cannot be empty"
        )

    system_prompt = """
You are VibeBuilder AI, an expert web developer.

You will receive an existing HTML website and an instruction describing
changes the user wants.

Modify the existing website according to the instruction.

Requirements:
- Preserve the existing website unless changes are requested.
- Return the complete updated HTML document.
- Use HTML5.
- Keep CSS inside <style>.
- Keep JavaScript inside <script> when needed.
- Keep the website responsive.
- Make the design visually polished.
- Use reliable external image URLs when images are needed.
- Do not use Markdown code fences.
- Do not explain anything.
- Return ONLY valid HTML.
"""

    user_prompt = f"""
Existing website:

{request.html}

User requested change:

{request.instruction}

Return the complete updated HTML document.
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
            max_tokens=5000,
        )

        website = response.choices[0].message.content

        if not website:
            raise Exception(
                "AI returned empty HTML."
            )

        website = website.strip()

        if website.startswith("```html"):
            website = website[7:]

        elif website.startswith("```"):
            website = website[3:]

        if website.endswith("```"):
            website = website[:-3]

        website = website.strip()

        return {
            "success": True,
            "html": website
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==================================================
# NETLIFY HELPERS
# ==================================================

def netlify_request(
    url,
    method="GET",
    data=None,
    content_type="application/json"
):

    headers = {
        "Authorization": f"Bearer {netlify_token}",
        "Accept": "application/json",
        "User-Agent": "VibeBuilder AI",
    }

    if content_type:
        headers["Content-Type"] = content_type

    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers=headers,
    )

    try:

        with urllib.request.urlopen(
            request
        ) as response:

            body = response.read()

            return json.loads(
                body.decode("utf-8")
            )

    except urllib.error.HTTPError as e:

        error_body = e.read().decode(
            "utf-8",
            errors="ignore"
        )

        raise Exception(
            f"Netlify API error {e.code}: "
            f"{error_body}"
        )


# ==================================================
# PUBLISH
# ==================================================

@app.post("/publish")
def publish_website(request: PublishRequest):

    if not request.html.strip():
        raise HTTPException(
            status_code=400,
            detail="Website HTML cannot be empty"
        )

    try:

        # --------------------------------------------------
        # 1. Create Netlify site
        # --------------------------------------------------

        site_name = (
            f"vibebuilder-"
            f"{secrets.token_hex(4)}"
        )

        create_data = json.dumps({
            "name": site_name
        }).encode("utf-8")

        site_data = netlify_request(
            "https://api.netlify.com/api/v1/sites",
            method="POST",
            data=create_data,
            content_type="application/json",
        )

        site_id = site_data.get("id")

        if not site_id:
            raise Exception(
                "Netlify did not return a site ID."
            )

        # --------------------------------------------------
        # 2. Prepare index.html
        # --------------------------------------------------

        html_bytes = request.html.encode(
            "utf-8"
        )

        # SHA1 is used by Netlify's file API
        file_hash = hashlib.sha1(
            html_bytes
        ).hexdigest()

        # --------------------------------------------------
        # 3. Ask Netlify which files it needs
        # --------------------------------------------------

        deploy_data = json.dumps({
            "files": {
                "index.html": file_hash
            }
        }).encode("utf-8")

        deploy_url = (
            f"https://api.netlify.com/api/v1/"
            f"sites/{site_id}/deploys"
        )

        deploy_info = netlify_request(
            deploy_url,
            method="POST",
            data=deploy_data,
            content_type="application/json",
        )

        required_files = deploy_info.get(
            "required",
            []
        )

        # --------------------------------------------------
        # 4. Upload required file
        # --------------------------------------------------

        if file_hash in required_files:

            upload_url = (
                f"https://api.netlify.com/api/v1/"
                f"deploys/{deploy_info['id']}"
                f"/files/index.html"
            )

            netlify_request(
                upload_url,
                method="PUT",
                data=html_bytes,
                content_type="application/octet-stream",
            )

        # --------------------------------------------------
        # 5. Determine URL
        # --------------------------------------------------

        public_url = (
            site_data.get("ssl_url")
            or site_data.get("url")
        )

        if not public_url:

            public_url = (
                f"https://"
                f"{site_name}"
                f".netlify.app"
            )

        # --------------------------------------------------
        # 6. Return result
        # --------------------------------------------------

        return {
            "success": True,
            "url": public_url,
            "site_id": site_id,
            "site_name": site_name,
            "deploy_id": deploy_info.get("id"),
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )