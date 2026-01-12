
import re
from bs4 import BeautifulSoup
from network_requests import fallback_kinopoisk_get, get_kinopoisk_film_info, search_kinopoisk
from telebot.types import InlineKeyboardMarkup
from telebot.types import InlineKeyboardButton


def get_times_word(count: int) -> str:
    """Возвращает правильное склонение слова 'раз'."""
    if count % 10 == 1 and count % 100 != 11:
        return "раз"
    elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
        return "раза"
    else:
        return "раз"


def format_movie_card(movie: dict) -> str:
    title = movie.get('Title', 'Неизвестно')
    year = movie.get('Year', '')
    imdb = movie.get('imdbRating', 'N/A')
    metascore = movie.get('Metascore', 'N/A')


    rotten = 'N/A'
    kinopoisk = 'N/A'
    for rating in movie.get('Ratings', []):
        if rating['Source'] == 'Rotten Tomatoes':
            rotten = rating['Value']
        if  rating['Source'] == 'Kinopoisk':
            kinopoisk = rating['Value']


    genre = movie.get('Genre', 'Неизвестно')
    runtime = movie.get('Runtime', 'Неизвестно')
    director = movie.get('Director', 'Неизвестно')
    actors = movie.get('Actors', 'Неизвестно')
    plot = movie.get('Plot', 'Описание отсутствует')
    box_office = movie.get('BoxOffice', 'N/A')

    card = f"""
🎬 <b>{title}</b> ({year})

⭐️ <b>Рейтинги:</b>
├ IMDb: <b>{imdb}</b>
├ Rotten Tomatoes: <b>{rotten}</b>
├ Kinopoisk: <b>{kinopoisk}</b>
└ Metascore: <b>{metascore}</b>

📋 <b>Информация:</b>
├ Жанр: {genre}
├ Время: {runtime}
├ Режиссёр: <i>{director}</i>
└ Актёры: <i>{actors}</i>

💰 Сборы: <b>{box_office}</b>

📖 <b>Сюжет:</b>
{plot}
"""
    return card.strip()


def convert_kinopoisk_to_omdb(kp: dict) -> dict:
    title = kp.get('nameRu') or kp.get('nameOriginal') or kp.get('nameEn') or 'Неизвестно'

    year = str(kp.get('year', 'N/A'))
    age_limits = kp.get('ratingAgeLimits', '')
    if age_limits:
        rated = age_limits.replace('age', '') + '+'
    else:
        rated = 'N/A'

    film_length = kp.get('filmLength')
    runtime = film_length if film_length else 'N/A'

    genres = kp.get('genres', [])
    genre_str = ', '.join(g['genre'].capitalize() for g in genres) if genres else 'N/A'

    plot = kp.get('description') or kp.get('shortDescription') or 'Описание отсутствует'
    poster = kp.get('posterUrl') or kp.get('posterUrlPreview') or 'N/A'

    ratings = []

    if kp.get('ratingKinopoisk'):
        ratings.append({
            'Source': 'Kinopoisk',
            'Value': f"{kp['ratingKinopoisk']}/10"
        })

    if kp.get('ratingImdb'):
        ratings.append({
            'Source': 'Internet Movie Database',
            'Value': f"{kp['ratingImdb']}/10"
        })

    if kp.get('ratingFilmCritics'):
        ratings.append({
            'Source': 'Film Critics',
            'Value': f"{kp['ratingFilmCritics']}/10"
        })

    imdb_rating = str(kp.get('ratingImdb', 'N/A'))

    return {
        'Title': title,
        'Year': year,
        'Rated': rated,
        'Runtime': runtime,
        'Genre': genre_str,
        'Director': 'N/A',
        'Actors': 'N/A',
        'Plot': plot,
        'Poster': poster,
        'Ratings': ratings,
        'imdbRating': imdb_rating,
        'BoxOffice': 'N/A'
    }


def get_most_wanted_film_id_css(html: str) -> tuple[str, str] | None:
    soup = BeautifulSoup(html, 'html.parser')

    data_id = soup.select_one('.element.most_wanted [data-id]')

    most_wanted = soup.find('div', class_='element most_wanted')
    if not most_wanted:
        return None

    info = most_wanted.find('div', class_='info')
    if not info:
        return None

    gray_spans = info.find_all('span', class_='gray')

    if not gray_spans:
        return None

    raw_title = gray_spans[0].get_text(strip=True)

    title = re.sub(r',?\s*\d+\s*мин\s*$', '', raw_title)


    if data_id:
        return (data_id['data-id'], title)

    return None


def create_watch_button(watch_url: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой просмотра."""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            text="▶️ Смотреть фильм",
            url=watch_url
        )
    )
    return keyboard


async def parse_kinopoisk(query: str) -> tuple[str|None, str|None, dict[str, str]|None]:
    html = await search_kinopoisk(query)
    film_info = get_most_wanted_film_id_css(html)
    if film_info is None:
        fallback_info = await fallback_kinopoisk_get(query)
        if fallback_info[0] is None:
            return None, None, None

        film_info = fallback_info

    kinopoisk_info = await get_kinopoisk_film_info(film_info[0])

    return f'https://flcksbr.top/film/{film_info[0]}', film_info[1], convert_kinopoisk_to_omdb(kinopoisk_info)
