

import os
import aiohttp
from urllib.parse import quote

API_KEY_IMDB = os.getenv('apikey')
API_KEY_KINOPOISK = os.getenv('API_KEY_KINOPOISK', '')


async def get(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            response.text
            return await response.json()


async def search_imdb(query: str):
    response = await get(f'http://www.omdbapi.com/?apikey={API_KEY_IMDB}&s={quote(query, safe="")}')
    if not response.get('Search'):
        return None
    imdb_id = response['Search'][0]['imdbID']
    main_info = await get(f'http://www.omdbapi.com/?apikey={API_KEY_IMDB}&i={imdb_id}')
    return main_info


async def search_kinopoisk(query: str):
    url = f'https://www.kinopoisk.ru/index.php?kp_query={quote(query, safe="")}'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


async def get_kinopoisk_film_info(data_id: str):
    url = f'https://kinopoiskapiunofficial.tech/api/v2.2/films/{data_id}'
    async with aiohttp.ClientSession(headers={'X-API-KEY':API_KEY_KINOPOISK}) as session:
        async with session.get(url) as response:
            return await response.json()


async def fallback_kinopoisk_get(query: str) -> tuple[str|None, str|None]:
    url = f'https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword?keyword={quote(query, safe="")}'
    async with aiohttp.ClientSession(headers={'X-API-KEY':API_KEY_KINOPOISK}) as session:
        async with session.get(url) as response:
            result = await response.json()
            result = result.get('films')
            if not result:
                return None, None
            return result[0].get("filmId"), result[0].get("nameEn", result[0].get("nameRu"))
