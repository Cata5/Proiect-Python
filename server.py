import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI(title = "CinemaWorld")

#creates and mounts static folder (Css, images)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

#configures the html template folder
os.makedirs("templates", exist_ok=True)
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Sends data to templates/index.html
    return templates.TemplateResponse(
        request = request,
        name = "index.html", 
        context = {"request": request, "message": "CinemaWorld is working!"}
    )