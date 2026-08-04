import os
import io
import base64
import httpx
from typing import Optional, Dict, Any
from pypdf import PdfReader
from config import settings

# Groq API Constants
GROQ_API_BASE = "https://api.groq.com/openai/v1"
GROQ_TEXT_MODEL = "llama-3.3-70b-versatile"
GROQ_VISION_MODEL = "llama-3.2-11b-vision-preview"
GROQ_EMBEDDING_MODEL = "nomic-embed-text-v1.5"


def _build_context(user_profile: Optional[Dict[str, Any]] = None) -> str:
    if not user_profile:
        return "No user profile available."

    safe_fields = {
        "name": user_profile.get("name"),
        "age": user_profile.get("age"),
        "category": user_profile.get("category"),
        "income": user_profile.get("income"),
        "occupation": user_profile.get("occupation"),
        "gender": user_profile.get("gender"),
        "state": user_profile.get("state"),
        "current_class": user_profile.get("current_class"),
        "education": user_profile.get("education"),
        "percentage": user_profile.get("percentage"),
    }
    lines = [f"{k}: {v}" for k, v in safe_fields.items() if v is not None]
    return "\n".join(lines) if lines else "No user profile available."


def _system_prompt_for_mode(mode: str) -> str:
    if mode == "career":
        return (
            "You are Career Path AI for HaryanaSarthi. "
            "Help students and job seekers with exams, colleges, internships, scholarships, jobs, "
            "learning path, next steps, and preparation guidance. "
            "Be concise, practical, and supportive. "
            "Prefer Haryana/government opportunity context when relevant. "
            "Do not invent exact eligibility facts not provided by the user or profile. "
            "If exact eligibility is unknown, clearly say it depends on platform eligibility results."
        )

    if mode == "life-event":
        return (
            "You are Life Event AI for HaryanaSarthi. "
            "Help citizens discover relevant government support based on situations like "
            "farmer support, women welfare, startup support, pension, social welfare, family support, and schemes. "
            "Give practical next actions and document guidance when possible. "
            "Do not invent exact official benefits if not provided. "
            "Keep the answer useful, citizen-friendly, and concise."
        )

    return (
        "You are the general multilingual AI chatbot for HaryanaSarthi. "
        "Answer in simple Hinglish unless the user clearly uses only Hindi or only English. "
        "Help users navigate the platform, understand opportunities, and ask follow-up questions. "
        "You may explain eligibility, platform features, and next actions in a clear way. "
        "Do not invent precise official facts."
    )


def extract_pdf_text(base64_data: str) -> str:
    """
    Parses base64 encoded PDF files and extracts text locally.
    """
    try:
        pdf_bytes = base64.b64decode(base64_data)
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        print(f"[PDF PARSE ERROR] Failed to extract text: {e}")
        return ""


async def ask_llm(message: str, mode: str = "general", user_profile: Optional[Dict[str, Any]] = None) -> str:
    """
    Asynchronously queries Groq text completions using Llama 3.3.
    """
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Groq API key not configured. Please add GROQ_API_KEY to the .env file."

    system_prompt = _system_prompt_for_mode(mode)
    profile_context = _build_context(user_profile)

    url = f"{GROQ_API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    user_content = f"User profile:\n{profile_context}\n\nUser message:\n{message}"
    payload = {
        "model": GROQ_TEXT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.2
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=25.0)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return "Groq AI rate limits exceeded. Please wait a moment and try again."
        return f"Groq request failed with status code {e.response.status_code}."
    except Exception as e:
        print(f"[LLM ERROR] Groq connection failed: {e}")
        return "Unable to connect to Groq AI server. Please check your internet connection."


async def analyze_document_async(file_data: str, mime_type: str, opportunity_name: str, user_profile: Optional[Dict[str, Any]] = None) -> str:
    """
    Asynchronously queries Groq Vision / Text completion models to parse documents.
    PDF files are parsed locally into text blocks. Image uploads use Llama 3.2 Vision.
    """
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Groq API key not configured. Please add GROQ_API_KEY to the .env file."

    profile_context = _build_context(user_profile)

    prompt = f"""
You are the Next Best Action AI for HaryanaSarthi.
The user is applying for: {opportunity_name}.
User profile:
{profile_context}

Analyze the provided document details carefully. Tell the user exactly:
1. What document they have uploaded (e.g. Aadhar card, marksheet, income certificate, etc.)
2. Is it sufficient for {opportunity_name}?
3. What *other* documents are they missing that they also need to upload or prepare for this specific opportunity?

Instructions:
- Keep the response short, practical, and in bullet points.
- If the uploaded document is not a known document type, gently tell them.
- Provide actionable next steps.
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    url = f"{GROQ_API_BASE}/chat/completions"

    # A. If PDF: Extract text locally and send to Groq Text completion
    if "pdf" in mime_type.lower():
        extracted_text = extract_pdf_text(file_data)
        if not extracted_text:
            return "Failed to parse text from the uploaded PDF. Please make sure the PDF contains readable text or upload a clean PNG/JPG screenshot instead."

        payload = {
            "model": GROQ_TEXT_MODEL,
            "messages": [
                {"role": "system", "content": "You analyze text extracted from applicant PDF attachments."},
                {
                    "role": "user", 
                    "content": f"{prompt}\n\n[EXTRACTED PDF DOCUMENT TEXT CONTENT]:\n{extracted_text}"
                }
            ],
            "temperature": 0.1
        }

    # B. If Image (PNG/JPEG): Send base64 inline image to Llama 3.2 Vision
    else:
        payload = {
            "model": GROQ_VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{file_data}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.1
        }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=40.0)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return "Groq AI is experiencing heavy load. Please try again in a few seconds."
        return f"Document analysis failed. Status: {e.response.status_code}."
    except Exception as e:
        print(f"[LLM ERROR] Document analysis failed: {e}")
        return "Unable to complete document analysis. Please check your network connection."


def get_embedding(text: str) -> list[float]:
    """
    Synchronously fetches vector embeddings from Groq using nomic-embed-text-v1.5.
    """
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[EMBEDDING ERROR] GROQ_API_KEY not configured.")
        return []

    url = f"{GROQ_API_BASE}/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_EMBEDDING_MODEL,
        "input": text
    }
    try:
        import requests
        response = requests.post(url, json=payload, headers=headers, timeout=12)
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]
    except Exception as e:
        print(f"[EMBEDDING ERROR] Groq embed request failed: {e}")
        return []


async def get_embedding_async(text: str) -> list[float]:
    """
    Asynchronously fetches vector embeddings from Groq using nomic-embed-text-v1.5.
    """
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
    if not api_key:
        return []

    url = f"{GROQ_API_BASE}/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_EMBEDDING_MODEL,
        "input": text
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=12)
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
    except Exception as e:
        print(f"[EMBEDDING ERROR] Groq async embed request failed: {e}")
        return []