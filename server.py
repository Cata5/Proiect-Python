import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from tmdb import fetch_random_movies

app = FastAPI(title = "CinemaWorld")

#creeaza si da "mount" la folderu static
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

#configureaza folderu de template-uri HTML
os.makedirs("templates", exist_ok=True)
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
#async ca programele/functiile care asteapta un raspuns sa nu blocheze totul
async def home(request: Request):
    # dam fetch la 10 filme de pe TMDB (filmele sunt alese random)
    movies = await fetch_random_movies(count=10)
    # trimite date la templates/index.html
    return templates.TemplateResponse(
        request = request,
        name = "index.html", 
        context={"request": request,"movies": movies}
    )