import os
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


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
NETLIFY_AUTH_TOKEN = os.getenv("NETLIFY_AUTH_TOKEN")

if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is missing from .env")

if not NETLIFY_AUTH_TOKEN:
    raise RuntimeError("NETLIFY_AUTH_TOKEN is missing from .env")


# ============================================================
# OPENROUTER
# ============================================================

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="VibeBuilder API",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        "message": "VibeBuilder backend is running",
        "status": "success"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ============================================================
# CLEAN HTML
# ============================================================

def clean_html(html: str) -> str:

    if not html:
        return ""

    html = html.strip()

    if html.startswith("```html"):
        html = html[7:]

    elif html.startswith("```HTML"):
        html = html[7:]

    elif html.startswith("```"):
        html = html[3:]

    if html.endswith("```"):
        html = html[:-3]

    return html.strip()


# ============================================================
# GENERATE WEBSITE
# ============================================================

@app.post("/generate")
def generate_website(request: GenerateRequest):

    system_prompt = """
You are VibeBuilder, a senior frontend engineer and award-winning web designer.

Your job is to generate a complete, production-quality website from the user's request.

The website must look like it was designed by a professional UI/UX designer, not like a generic AI-generated template.

========================
CORE OUTPUT RULES
========================

- Return ONLY the complete HTML document.
- Start with <!DOCTYPE html>
- End with </html>
- Use semantic HTML5.
- Put all CSS inside <style>.
- Put JavaScript inside <script> when needed.
- Do not use Markdown.
- Do not explain anything outside the HTML.
- Do not use Lorem ipsum.
- Use realistic, meaningful content relevant to the user's request.
- The final result must be immediately usable.

========================
DESIGN QUALITY
========================

Create a strong visual hierarchy.

Use:

- A professional font stack or Google Fonts when appropriate.
- Clear heading hierarchy.
- Comfortable line-height.
- Consistent spacing.
- A centered max-width content container.
- Balanced whitespace.
- Consistent border radius.
- Subtle shadows.
- Carefully chosen colors.
- Professional buttons.
- Clear visual separation between sections.

Do NOT:

- Make everything centered unnecessarily.
- Use huge empty spaces.
- Use excessive gradients.
- Use too many colors.
- Use random font sizes.
- Use repetitive cards everywhere.
- Make every section look identical.
- Create an overly simplistic template.

========================
LAYOUT
========================

Build a complete page structure appropriate for the request.

When appropriate include:

1. Navbar
2. Hero section
3. Supporting information
4. Features/services
5. About/content section
6. Statistics or social proof
7. Testimonials
8. Pricing when relevant
9. Call-to-action
10. Footer

Do not blindly include every section.

Choose sections based on the user's request.

Each section should have a distinct visual purpose.

========================
HERO SECTION
========================

The hero should immediately communicate:

- What the website/product/business is.
- The main value proposition.
- A strong primary CTA.
- A secondary CTA when appropriate.
- Supporting visual content when useful.

Use strong typography and balanced spacing.

The hero should feel visually impressive without becoming cluttered.

========================
COMPONENT DESIGN
========================

Buttons should have:

- Clear hierarchy.
- Good padding.
- Rounded corners.
- Hover states.
- Smooth transitions.

Cards should have:

- Consistent spacing.
- Clear hierarchy.
- Subtle borders or shadows.
- Hover effects when appropriate.

Navigation should:

- Be visually clean.
- Clearly indicate important actions.
- Work properly on mobile.

========================
RESPONSIVE DESIGN
========================

The website MUST work well on:

- Desktop
- Tablet
- Mobile

Use responsive CSS with appropriate breakpoints.

Avoid:

- Horizontal overflow.
- Fixed-width layouts that break on mobile.
- Text becoming too small.
- Images overflowing containers.
- Navigation becoming unusable.

========================
VISUAL STYLE
========================

Choose a coherent visual direction based on the user's request.

Possible styles include:

- Modern SaaS
- Premium corporate
- Minimal portfolio
- Creative agency
- Luxury
- E-commerce
- Startup
- Technology
- Restaurant
- Education
- Healthcare
- Finance

Do not force one style onto every website.

Create a consistent design system for each website.

========================
IMAGES
========================

Images are important, but RELEVANCE is more important than simply having an image.

Before selecting ANY image, first identify:

1. The exact subject of the website.
2. The brand, business, product, service, or industry.
3. The purpose of the section where the image will appear.
4. What a real professional website in that industry would normally show.

The image MUST clearly match the website subject AND the section.

========================
SUBJECT RELEVANCE RULES
========================

NEVER use a generic professional-looking image just because it looks attractive.

Restaurant / Food website:
- Use food, dishes, burgers, fried chicken, fries, drinks, ingredients, chefs, kitchens, dining, or restaurant interiors.
- Do NOT use office workers, laptops, software developers, business meetings, corporate buildings, or generic teamwork images.

KFC / Fried Chicken website:
- Use fried chicken, chicken burgers, fries, chicken meals, food buckets, restaurant food, restaurant interiors, food preparation, or dining.
- Do NOT use office workers, people using computers, software developers, corporate meetings, generic business teams, or unrelated technology imagery.

Gym / Fitness website:
- Use gyms, athletes, workouts, exercise equipment, running, strength training, or fitness activities.
- Do NOT use unrelated corporate or office images.

Technology / SaaS website:
- Use software, computers, AI, developers, dashboards, digital products, servers, or technology environments.

Travel website:
- Use destinations, beaches, mountains, landmarks, hotels, cities, landscapes, or travel activities.

Education website:
- Use students, classrooms, teachers, books, laboratories, learning environments, or educational activities.

Healthcare website:
- Use doctors, hospitals, medical equipment, healthcare professionals, clinics, or patient care.

Real Estate website:
- Use houses, apartments, buildings, interiors, architecture, or property photography.

Portfolio / Creative Agency:
- Use design work, creative workspaces, artwork, photography, branding, or relevant project imagery.

========================
IMAGE SELECTION
========================

Do NOT choose an image merely because it is:

- Professional
- Beautiful
- Modern
- Corporate
- High quality

It must be relevant to the actual website.

For every image ask:

"Would a visitor immediately understand why this image belongs on this website?"

If NO:

- Do not use it.
- Find a more relevant image.
- Or use a CSS-based visual instead.

Do NOT use generic "office", "business", "teamwork", "corporate", or "technology" imagery unless the website is actually about those subjects.

========================
IMAGE URL RULES
========================

- Use HTTPS image URLs only.
- Do NOT invent image URLs.
- Do NOT use fake domains.
- Do NOT use local file paths.
- Do NOT use authentication-required image URLs.
- Do NOT use webpage URLs as image URLs.
- Prefer stable public image URLs.
- Prefer direct images from images.unsplash.com when appropriate.
- Do not use random images simply to fill empty space.
- Use a reasonable number of images.
- Never add dozens of unnecessary images.

If you cannot confidently provide a valid AND relevant image URL:

DO NOT use an unrelated image.

Instead, create a visually attractive CSS-based visual or placeholder that matches the website subject.

For example, if a restaurant website does not have a suitable food image, create a tasteful food-themed CSS visual rather than showing an unrelated office photograph.

========================
IMAGE IMPLEMENTATION
========================

For every image:

- Add meaningful alt text describing the actual image.
- Use width: 100% where appropriate.
- Use an appropriate height or aspect-ratio.
- Use object-fit: cover for image cards.
- Use border-radius consistent with the design.
- Make images responsive.
- Prevent images from overflowing their containers.

The alt text must match the actual subject.

Bad for a restaurant:

<img src="..." alt="Professional business team">

Good:

<img src="..." alt="Crispy fried chicken served with fries">

========================
IMAGE FALLBACK
========================

For externally loaded images, add a graceful fallback using the image error event.

If an image fails to load:

- Do not display the browser broken-image icon.
- Hide or replace the failed image.
- Show a visually appropriate CSS fallback.
- Keep the layout intact.
- The fallback must still fit the website's subject and design.

Do not replace a failed restaurant image with a generic office image.

========================
FINAL IMAGE CHECK
========================

Before returning the HTML:

1. Identify every image used.
2. Check whether each image matches the website subject.
3. Check whether it matches the section content.
4. Remove unrelated images.
5. Replace unsuitable images with relevant ones or CSS visuals.
6. Ensure the page still looks complete without external images.

NEVER use an unrelated image simply because it is attractive.

========================
INTERACTIONS
========================

Add subtle professional interactions where useful:

- Hover transitions
- Button animations
- Card hover effects
- Smooth scrolling
- Mobile navigation
- FAQ interactions
- Simple counters or UI interactions

For externally loaded images, always add a graceful fallback using the image error event.

If an image fails to load:

- Do not leave the browser broken-image icon visible.
- Hide the failed image or replace it with a CSS-based visual fallback.
- Keep the image container's dimensions and layout intact.
- Make the fallback match the website's design.
- Do not replace a failed image with another unverified URL.

Do not add unnecessary JavaScript.

========================
ACCESSIBILITY
========================

Use:

- Semantic elements.
- Proper button elements.
- Accessible labels.
- Good color contrast.
- Alt text for images.
- Keyboard-friendly controls where applicable.

========================
FUNCTIONALITY
========================

Navigation and buttons should work where appropriate.

Use:

- Anchor links for page sections.
- External links for external destinations.
- Functional forms where appropriate.
- Smooth scrolling for internal navigation.

Do not create fake functionality that cannot work.

========================
FINAL QUALITY CHECK
========================

Before returning the HTML, mentally inspect the website as a professional designer.

Check:

- Does the page have a strong visual hierarchy?
- Does the hero look impressive?
- Are spacing and typography consistent?
- Are sections visually distinct?
- Does the color palette make sense?
- Are buttons attractive?
- Does the page look good on mobile?
- Is there excessive empty space?
- Does anything look like a generic AI template?
- Are there unnecessary sections?
- Does the website feel complete?

Fix any problems before returning the HTML.

Return ONLY the final HTML document.
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",

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

        html = clean_html(html)

        return {
            "html": html
        }

    except Exception as e:

        print("Generate error:", str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# EDIT WEBSITE
# ============================================================

@app.post("/edit")
def edit_website(request: EditRequest):

    system_prompt = """
You are VibeBuilder, a senior frontend engineer and professional UI/UX designer.

You will receive an existing HTML website and a requested modification.

Your job is to intelligently modify the existing website while preserving everything that already works.

========================
CORE RULE
========================

Make the user's requested change accurately.

Do NOT unnecessarily rebuild the entire website.

Preserve:

- Existing content.
- Existing sections.
- Existing functionality.
- Existing navigation.
- Existing JavaScript.
- Existing responsive behavior.

Only change what is necessary unless the user explicitly requests a redesign.

========================
DESIGN IMPROVEMENTS
========================

If the user requests a visual or design improvement:

- Improve spacing.
- Improve typography.
- Improve visual hierarchy.
- Improve color consistency.
- Improve buttons.
- Improve cards.
- Improve section layouts.
- Improve responsive behavior.
- Add subtle animations where appropriate.

Keep the existing design direction unless the user asks for a completely different style.

========================
REDESIGN REQUESTS
========================

If the user asks for:

- "Make it more modern"
- "Make it professional"
- "Improve the design"
- "Make it look better"
- "Make it premium"
- "Redesign the website"

Then perform a thoughtful UI/UX improvement.

Focus on:

- Better typography.
- Better spacing.
- Stronger hero section.
- Better navigation.
- Better cards.
- Better buttons.
- Better color palette.
- Better section hierarchy.
- More polished responsive layouts.
- Subtle hover and transition effects.

Do not destroy useful existing content.

========================
RESPONSIVE DESIGN
========================

The updated website must remain fully responsive on:

- Desktop
- Tablet
- Mobile

Prevent:

- Horizontal overflow.
- Broken navigation.
- Overlapping elements.
- Fixed layouts that fail on mobile.
- Images overflowing their containers.

========================
IMAGES
========================

When adding or replacing images during an edit:

- Use HTTPS direct image URLs only.
- Prefer the known stable images.unsplash.com URLs already present in the website.
- Never invent image URLs.
- Never replace a working image with an unverified URL.
- If a suitable reliable image cannot be used, create a CSS-based visual instead.
- Preserve graceful image error fallbacks.

========================
IMAGE RELEVANCE
========================

When editing an existing website:

- Preserve images that are clearly relevant to the website.
- If an existing image is unrelated to the website subject, replace it with a relevant image or a CSS-based visual.
- Never introduce generic office, business, teamwork, or technology images into an unrelated website.
- For restaurant websites, keep imagery focused on food, dishes, restaurants, kitchens, chefs, or dining.
- For KFC or fried-chicken websites, keep imagery focused on fried chicken, chicken meals, burgers, fries, drinks, restaurants, or food preparation.
- Any new image must be relevant to both the website and the section.
- Use HTTPS direct image URLs only.
- Do not invent image URLs.
- If a suitable image cannot be confidently selected, use a CSS-based visual instead.
- Add graceful image error fallbacks so failed external images do not show broken-image icons.
- Preserve the layout if an image fails to load.

========================
CODE QUALITY
========================

Keep the HTML clean and valid.

Use:

- Semantic HTML5.
- CSS inside <style>.
- JavaScript inside <script> when necessary.

Do not introduce unnecessary dependencies.

========================
FUNCTIONALITY
========================

Preserve existing functionality unless the user specifically asks to change it.

Do not remove:

- Working navigation.
- Forms.
- Buttons.
- Interactive components.
- Existing JavaScript behavior.

========================
FINAL QUALITY CHECK
========================

Before returning the result, verify:

- The requested change was implemented.
- Existing functionality still works.
- The design remains coherent.
- The page is responsive.
- No unnecessary content was removed.
- No broken HTML was introduced.
- The result looks professionally designed.

Return ONLY the complete updated HTML document.

Start with <!DOCTYPE html>
End with </html>
Do not use Markdown.
Do not provide explanations.
"""

    user_prompt = f"""
Here is the existing website HTML:

---------------- EXISTING HTML ----------------

{request.html}

---------------- END EXISTING HTML ----------------

Here is the user's requested modification:

{request.instruction}

Modify the website according to the request.

Return ONLY the complete updated HTML document.
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",

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

        html = clean_html(html)

        return {
            "html": html
        }

    except Exception as e:

        print("Edit error:", str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# PUBLISH TO NETLIFY
# ============================================================

@app.post("/publish")
def publish_website(request: PublishRequest):

    if not request.html:
        raise HTTPException(
            status_code=400,
            detail="HTML content is empty"
        )

    site_name = f"vibebuilder-{secrets.token_hex(4)}"

    headers = {
        "Authorization": f"Bearer {NETLIFY_AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

    # --------------------------------------------------------
    # CREATE NETLIFY SITE
    # --------------------------------------------------------

    create_data = json.dumps({
        "name": site_name
    }).encode("utf-8")

    create_request = urllib.request.Request(
        "https://api.netlify.com/api/v1/sites",
        data=create_data,
        headers=headers,
        method="POST"
    )

    try:

        with urllib.request.urlopen(create_request) as response:

            site_data = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as e:

        error_body = e.read().decode("utf-8")

        raise HTTPException(
            status_code=e.code,
            detail=f"Netlify error: {error_body}"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    site_id = site_data.get("id")

    site_url = (
        site_data.get("ssl_url")
        or site_data.get("url")
    )

    if not site_id:

        raise HTTPException(
            status_code=500,
            detail="Netlify did not return a site ID"
        )

    # --------------------------------------------------------
    # FILE HASH
    # --------------------------------------------------------

    html_bytes = request.html.encode("utf-8")

    file_hash = hashlib.sha1(
        html_bytes
    ).hexdigest()

    files = {
        "/index.html": file_hash
    }

    # --------------------------------------------------------
    # CREATE DEPLOY
    # --------------------------------------------------------

    deploy_data = json.dumps({
        "files": files
    }).encode("utf-8")

    deploy_request = urllib.request.Request(
        f"https://api.netlify.com/api/v1/sites/{site_id}/deploys",
        data=deploy_data,
        headers=headers,
        method="POST"
    )

    try:

        with urllib.request.urlopen(deploy_request) as response:

            deploy_response = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as e:

        error_body = e.read().decode("utf-8")

        raise HTTPException(
            status_code=e.code,
            detail=f"Netlify deploy error: {error_body}"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    deploy_id = deploy_response.get("id")

    if not deploy_id:

        raise HTTPException(
            status_code=500,
            detail="Netlify did not return a deploy ID"
        )

    # --------------------------------------------------------
    # UPLOAD INDEX.HTML
    # --------------------------------------------------------

    upload_headers = {
        "Authorization": f"Bearer {NETLIFY_AUTH_TOKEN}",
        "Content-Type": "application/octet-stream"
    }

    upload_request = urllib.request.Request(
        f"https://api.netlify.com/api/v1/deploys/{deploy_id}/files/index.html",
        data=html_bytes,
        headers=upload_headers,
        method="PUT"
    )

    try:

        with urllib.request.urlopen(upload_request) as response:

            response.read()

    except urllib.error.HTTPError as e:

        error_body = e.read().decode("utf-8")

        raise HTTPException(
            status_code=e.code,
            detail=f"Netlify upload error: {error_body}"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    return {
        "success": True,
        "site_id": site_id,
        "deploy_id": deploy_id,
        "url": site_url
    }