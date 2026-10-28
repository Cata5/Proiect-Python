import os
import json
import re
from typing import List
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from tmdb import fetch_random_movies, search_movies_by_title, get_genres, httpx
from MovieRecommendSystem import ask_unsloth_async

load_dotenv()

app = FastAPI(title="CinemaWorld")

# Configurare fisiere statice si template-uri HTML
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class RecommendationRequest(BaseModel):
    genres: List[str] = []
    liked_movies: List[str] = []


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Pagina principala: afiseaza filmele din cinema si lista de genuri."""
    movies = await fetch_random_movies(count=10)
    async with httpx.AsyncClient() as client:
        genres = await get_genres(client)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request, "movies": movies, "genres": genres}
    )


@app.get("/api/search")
async def search_movie(q: str = ""):
    """Cauta filme dupa titlu folosind TMDB."""
    movies = await search_movies_by_title(title=q, count=5)
    return {"movies": movies}


@app.post("/api/ai-recommend")
async def ai_recommend(req: RecommendationRequest):
    """
    Trimite preferintele utilizatorului la Unsloth AI si returneaza 3 carduri de filme din TMDB.
    """
    genres_text = ", ".join(req.genres) if req.genres else "action, adventure"
    liked_text = ", ".join(req.liked_movies) if req.liked_movies else "popular movies"

    # 1. Simple prompt: ask the model for 3 titles in JSON format
    prompt = (
        "You are a movie recommendation expert. Recommend exactly 3 movies based on "
        f"these preferred genres: {genres_text}\n"
        f"Movies the user already likes: {liked_text}\n\n"

        "REQUIREMENTS:\n"
        "1. Recommend exactly 3 distinct, real, released movies.\n"
        "2. Match the user's preferred genres and infer their taste from the liked movies.\n"
        "3. NEVER recommend a movie that appears in the liked movies list. "
        "Compare titles case-insensitively and account for minor title variations.\n"
        "4. Prioritize well-known, recognizable movies with established audiences. "
        "Avoid obscure, fictional, unreleased, or incorrectly named titles.\n"
        "5. Choose movies the user is likely to enjoy, not simply the most popular movies.\n"
        "6. Give each movie a concise, specific reason that explains why it matches "
        "the user's preferences. Avoid generic explanations.\n"
        "7. Ensure all 3 recommendations are different movies.\n\n"

        "OUTPUT RULES:\n"
        "- Respond ONLY with a valid JSON array containing exactly 3 objects.\n"
        "- Each object must contain exactly two string fields: 'title' and 'reason'.\n"
        "- Use double quotes for all JSON keys and string values.\n"
        "- Do not include Markdown, code fences, comments, or text outside the JSON array.\n"
        "- Ensure the output can be parsed directly using Python's json.loads().\n\n"

        "Required format:\n"
        '[{"title": "Movie Title", "reason": "Why this movie fits the user"}, '
        '{"title": "Movie Title", "reason": "Why this movie fits the user"}, '
        '{"title": "Movie Title", "reason": "Why this movie fits the user"}]'
    )

    try:
        # 2. Apelam Unsloth AI
        data = await ask_unsloth_async(prompt)
        ai_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        # 3. Extragem lista JSON din raspunsul AI
        match = re.search(r"\[.*\]", ai_text, re.DOTALL)
        items = json.loads(match.group(0)) if match else []

        # 4. Cautam fiecare film in TMDB pentru poster si detalii
        cards = []
        for item in items[:3]:
            title = item.get("title", "")
            results = await search_movies_by_title(title, count=1)

            if results:
                movie = results[0]
                movie["reason"] = item.get("reason", "")
                cards.append(movie)

        return {"movies": cards}

    except Exception as e:
        return {"error": str(e)}
