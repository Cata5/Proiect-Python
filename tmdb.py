import os
import random
import httpx
from dotenv import load_dotenv
#citim cheia din .env
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# Mock showtimes to pick from for our cinema UI
SHOWTIME_OPTIONS = ["13:30", "15:45", "18:00", "20:15", "22:30"]

_GENRE_CACHE = {}
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
    #global modifica o variabila care e declarata global (in afara functiei)
    global _GENRE_CACHE
    if _GENRE_CACHE:
        return _GENRE_CACHE
    url = f"{BASE_URL}/genre/movie/list"
    #parametrii cererii.
    headers, params = get_auth_headers_and_params()
    params["language"] = "en-US"

    try:
        response = await client.get(url, params=params,headers=headers)
        if response.status_code == 200:
            data = response.json()
            _GENRE_CACHE = {g["id"]: g["name"] for g in data.get("genres", [])}
    except Exception as e:
        print(e)
    return _GENRE_CACHE


async def fetch_random_movies(count: int = 10) -> list:
    global _MOVIES_CACHE
    #daca avem deja filme nu le mai dam refresh (se da refresh la file doar la repornirea serverului)
    if _MOVIES_CACHE:
        return _MOVIES_CACHE
    if not TMDB_API_KEY:
        print("Warning: TMDB_API_KEY is not set in .env")
        return []

    random_page = random.randint(1, 5)
    #params for fetching a TMDB page and the movies on it
    headers,params = get_auth_headers_and_params()
    params["language"] = "en-US"
    params["page"] = random_page
    params["sort_by"] = "popularity.desc"
    params["vote_count.gte"] = 100

    #creating a HTTP async client that it closes automatically when we finish using it.
    async with httpx.AsyncClient() as client:

        genres_map = await get_genres(client)
        
        response = await client.get(f"{BASE_URL}/discover/movie", params=params ,headers=headers)
        if response.status_code != 200:
            print(f"Eroare TMDB: {response.status_code} {response.text}") # ca să vedem dacă e vreo problemă cu cheia
            return []
        results = response.json().get("results", [])
        
        # Only take movies that have a poster image
        valid_movies = [m for m in results if m.get("poster_path")]
        # Sample 10 random movies (or whatever count is requested)
        sampled = random.sample(valid_movies, min(count, len(valid_movies)))
        # Format movie dict for the template
        formatted_movies = []
        for movie in sampled:
            # Get up to 2 genre names
            movie_genres = [
                genres_map.get(gid) for gid in movie.get("genre_ids", [])[:2]
                if gid in genres_map
            ]
            
            # Format release year from "YYYY-MM-DD"
            release_date = movie.get("release_date", "")
            year = release_date.split("-")[0] if release_date else "N/A"
            
            # Pick 3 random showtimes for this movie
            showtimes = sorted(random.sample(SHOWTIME_OPTIONS, 3))
            formatted_movies.append({
                "id": movie.get("id"),
                "title": movie.get("title"),
                "overview": movie.get("overview"),
                "poster_url": f"{IMAGE_BASE_URL}{movie.get('poster_path')}",
                "rating": f"★ {movie.get('vote_average', 0):.1f}",
                "year": year,
                "genres": movie_genres,
                "showtimes": showtimes,
            })
        _MOVIES_CACHE = formatted_movies
        return _MOVIES_CACHE
