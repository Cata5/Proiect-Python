import os
import random
import httpx
from dotenv import load_dotenv
import json
from models import Film

#citim cheia din .env
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# Mock showtimes to pick from for our cinema UI
SHOWTIME_OPTIONS = ["13:30", "15:45", "18:00", "20:15", "22:30"]
_GENRE_CACHE = {}
_MOVIES_CACHE = []

try:
    with open("database.json", "r", encoding="utf-8") as f:
        _MOVIES_CACHE = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Cache miss or empty database.json: {e}")
    _MOVIES_CACHE = []

def get_auth_headers_and_params():
    # Dacă e token lung (v4 Bearer)
    if not TMDB_API_KEY:
        return {}, {}
    if len(TMDB_API_KEY) > 40:
        return {"Authorization": f"Bearer {TMDB_API_KEY}"}, {}
    # Altfel este v3 API Key tradițional
    return {}, {"api_key": TMDB_API_KEY}

async def get_genres(client: httpx.AsyncClient) -> dict:
    global _GENRE_CACHE
    if _GENRE_CACHE:
        return _GENRE_CACHE
    url = f"{BASE_URL}/genre/movie/list"
    headers, params = get_auth_headers_and_params()
    params["language"] = "en-US"

    try:
        response = await client.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            _GENRE_CACHE = {g["id"]: g["name"] for g in data.get("genres", [])}
    except Exception as e:
        print(e)
    return _GENRE_CACHE


async def fetch_random_movies(count: int = 10) -> list:
    global _MOVIES_CACHE
    if _MOVIES_CACHE:
        return _MOVIES_CACHE
    if not TMDB_API_KEY:
        print("Warning: TMDB_API_KEY is not set in .env")
        return []

    headers, params = get_auth_headers_and_params()
    params["language"] = "en-US"
    params["page"] = 1
    params["release_date"] = 2026
    params["vote_count.gte"] = 100

    async with httpx.AsyncClient() as client:
        genres_map = await get_genres(client)
        
        response = await client.get(f"{BASE_URL}/discover/movie", params=params, headers=headers)
        if response.status_code != 200:
            print(f"Eroare TMDB: {response.status_code} {response.text}")
            return []
        results = response.json().get("results", [])
        
        valid_movies = [m for m in results if m.get("poster_path")]
        sampled = random.sample(valid_movies, min(count, len(valid_movies)))
        
        formatted_movies = []
        for movie in sampled:
            movie_genres = [
                genres_map.get(gid) for gid in movie.get("genre_ids", [])[:2]
                if gid in genres_map
            ]
            
            release_date = movie.get("release_date", "")
            year = release_date.split("-")[0] if release_date else "N/A"
            showtimes = sorted(random.sample(SHOWTIME_OPTIONS, 3))
            
            # Folosim clasa Film cerută de profesor
            film_obiect = Film(
                id=movie.get("id"),
                title=movie.get("title"),
                overview=movie.get("overview"),
                poster_url=f"{IMAGE_BASE_URL}{movie.get('poster_path')}",
                rating=f"★ {movie.get('vote_average', 0):.1f}",
                year=year,
                genres=movie_genres,
                showtimes=showtimes,
                price=f"{random.randint(50,80)} RON"
            )
            formatted_movies.append(film_obiect.to_dict())

        _MOVIES_CACHE = formatted_movies
        try:
            with open("database.json", "w", encoding="utf-8") as f:
                json.dump(_MOVIES_CACHE, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Eroare la salvarea bazei de date: {e}")
        return _MOVIES_CACHE



async def search_movies_by_title(title: str, count: int = 5) -> list:
    """Search for movies on TMDB by title (useful for finding liked movies or model recommendations)."""
    if not TMDB_API_KEY or not title.strip():
        return []

    headers, params = get_auth_headers_and_params()
    params["language"] = "en-US"
    params["query"] = title.strip()
    params["page"] = 1

    async with httpx.AsyncClient() as client:
        genres_map = await get_genres(client)
        try:
            response = await client.get(f"{BASE_URL}/search/movie", params=params, headers=headers)
            if response.status_code != 200:
                return []
            results = response.json().get("results", [])
            valid_movies = [m for m in results if m.get("poster_path")][:count]

            movies = []
            for movie in valid_movies:
                movie_genres = [
                    genres_map.get(gid) for gid in movie.get("genre_ids", [])[:2]
                    if gid in genres_map
                ]
                release_date = movie.get("release_date", "")
                year = release_date.split("-")[0] if release_date else "N/A"
                showtimes = sorted(random.sample(SHOWTIME_OPTIONS, 3))

                # Folosim clasa Film și aici
                film_obiect = Film(
                    id=movie.get("id"),
                    title=movie.get("title"),
                    overview=movie.get("overview"),
                    poster_url=f"{IMAGE_BASE_URL}{movie.get('poster_path')}",
                    rating=f"★ {movie.get('vote_average', 0):.1f}",
                    year=year,
                    genres=movie_genres,
                    showtimes=showtimes,
                    price=f"{random.randint(50,80)} RON"
                )
                movies.append(film_obiect.to_dict())
            return movies
        except Exception as e:
            print(f"Error searching movies by title: {e}")
            return []
