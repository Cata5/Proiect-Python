import os
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("UNSLOTH_API", "http://127.0.0.1:8888/v1").rstrip("/")
URL = f"{BASE_URL}/chat/completions" if not BASE_URL.endswith("/chat/completions") else BASE_URL
MODEL = os.getenv("MODEL")


def ask_unsloth(prompt: str) -> dict:
    """Sends a prompt to Unsloth and returns the full JSON response."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "enable_tools": True,
        "enabled_tools": ["web_search"],
        "permission_mode": "off",
        "stream": False,
        "cache_prompt": False
    }

    headers = {
        "Authorization": "Bearer not-needed",
        "Content-Type": "application/json"
    }

    response = httpx.post(URL, json=payload, headers=headers, timeout=120.0)
    response.raise_for_status()
    return response.json()


async def ask_unsloth_async(prompt: str) -> dict:
    """Async version of ask_unsloth for FastAPI non-blocking endpoints."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "enable_tools": True,
        "enabled_tools": ["web_search"],
        "permission_mode": "off",
        "stream": False,
        "cache_prompt": False
    }

    headers = {
        "Authorization": "Bearer not-needed",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


def get_recommendation_text(prompt: str) -> str:
    """Helper that queries Unsloth and returns only the model's text answer."""
    data = ask_unsloth(prompt)
    return data.get("choices", [{}])[0].get("message", {}).get("content", "")


# if __name__ == "__main__":
#     prompt = (
#         "For these genres: action, thriller, adventure and these liked movies: "
#         "The Maze Runner, War of the Worlds, The Beekeeper, give me 3 recommendations "
#         "with similar movies. Search online for an updated movie list and return the titles."
#     )
#     print(f"Sending prompt:\n{prompt}\n")

#     try:
#         answer = get_recommendation_text(prompt)
#         print("Model Answer:\n")
#         print(answer)
#     except Exception as e:
#         print(f"Error: {e}")
