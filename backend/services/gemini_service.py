import os
import requests
from typing import Optional, Dict, Any

GEMINI_MODEL = "gemini-2.0-flash"


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


def ask_gemini(message: str, mode: str = "general", user_profile: Optional[Dict[str, Any]] = None) -> str:
    # Use environment variable from .env
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return (
            "Gemini API key not configured. Please add GEMINI_API_KEY to the .env file."
        )

    system_prompt = _system_prompt_for_mode(mode)
    profile_context = _build_context(user_profile)

    final_prompt = f"""
{system_prompt}

User profile:
{profile_context}

User message:
{message}

Instructions:
- Keep response helpful and practical.
- Use short paragraphs or bullets only if really needed.
- If user asks what to do next, give step-by-step next actions.
- If user asks in Hinglish, reply in Hinglish.
"""

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={api_key}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": final_prompt}
                ]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        candidates = data.get("candidates", [])
        if not candidates:
            return "No response received from Gemini."

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            return "No response text received from Gemini."

        text = "".join(part.get("text", "") for part in parts).strip()
        return text or "Gemini returned an empty response."

    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            return "AI is receiving too many requests right now. Please wait a moment and try again."
        return "Gemini request failed. Please try again later."
    except requests.RequestException:
        return "Unable to connect to Gemini AI. Please check your internet connection."


def analyze_document(file_data: str, mime_type: str, opportunity_name: str, user_profile: Optional[Dict[str, Any]] = None) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Gemini API key not configured. Please add GEMINI_API_KEY to the .env file."

    profile_context = _build_context(user_profile)

    final_prompt = f"""
You are the Next Best Action AI for HaryanaSarthi.
The user is applying for: {opportunity_name}.
User profile:
{profile_context}

The user has uploaded a document (provided as an attachment).
Analyze the document carefully. Tell the user exactly:
1. What document they have uploaded (e.g. Aadhar card, mark sheet, etc.)
2. Is it sufficient for {opportunity_name}?
3. What *other* documents are they missing that they also need to upload or prepare for this specific opportunity? 

Instructions:
- Keep the response short, practical, and in bullet points.
- If the uploaded document is not a known document type, gently tell them.
- Provide actionable next steps.
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": final_prompt},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": file_data
                        }
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, timeout=45)
        response.raise_for_status()
        data = response.json()

        candidates = data.get("candidates", [])
        if not candidates:
            return "No response received from Gemini."

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            return "No response text received from Gemini."

        text = "".join(part.get("text", "") for part in parts).strip()
        return text or "Gemini returned an empty response."

    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            return "AI is receiving too many requests right now. Please wait a moment and try again."
        return "Document analysis failed. Please try again later."
    except requests.RequestException:
        return "Unable to connect to Gemini AI. Please check your internet connection."