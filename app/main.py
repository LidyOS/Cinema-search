from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from format_card import format_movie_card, parse_kinopoisk
from network_requests import search_imdb

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "result": None,
        "error": None
    })


@app.post("/search", response_class=HTMLResponse)
async def search(request: Request, query: str = Form(...)):
    try:
        watch_url, original_title, kp_info = await parse_kinopoisk(query)

        film_info = kp_info
        if original_title:
            imdb_info = await search_imdb(original_title)
            if imdb_info:
                film_info = imdb_info

        if not film_info or not watch_url:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "result": None,
                "error": "Ничего не найдено"
            })

        card = format_movie_card(film_info)
        poster = film_info.get("Poster")

        return templates.TemplateResponse("index.html", {
            "request": request,
            "result": {
                "card": card,
                "poster": poster,
                "watch_url": watch_url
            },
            "error": None
        })

    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "result": None,
            "error": str(e)
        })
