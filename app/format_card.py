import re
from bs4 import BeautifulSoup
from network_requests import fallback_kinopoisk_get, get_kinopoisk_film_info, search_kinopoisk


def get_times_word(count: int) -> str:
    """Возвращает правильное склонение слова 'раз'."""
    if count % 10 == 1 and count % 100 != 11:
        return "раз"
    elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
        return "раза"
    else:
        return "раз"


def format_movie_card(movie: dict) -> str:
    """Возвращает карточку фильма в HTML для сайта."""
    title = movie.get('Title', 'Неизвестно')
    year = movie.get('Year', '')
    imdb = movie.get('imdbRating', 'N/A')
    metascore = movie.get('Metascore', 'N/A')

    rotten = 'N/A'
    kinopoisk = 'N/A'
    for rating in movie.get('Ratings', []):
        if rating['Source'] == 'Rotten Tomatoes':
            rotten = rating['Value']
        if rating['Source'] == 'Kinopoisk':
            kinopoisk = rating['Value']

    genre = movie.get('Genre', 'Неизвестно')
    runtime = movie.get('Runtime', 'Неизвестно')
    director = movie.get('Director', 'Неизвестно')
    actors = movie.get('Actors', 'Неизвестно')
    plot = movie.get('Plot', 'Описание отсутствует')
    box_office = movie.get('BoxOffice', 'N/A')

    card = f"""
<h2>{title} ({year})</h2>

<p><b>Рейтинги:</b><br>
IMDb: {imdb}<br>
Rotten Tomatoes: {rotten}<br>
Kinopoisk: {kinopoisk}<br>
Metascore: {metascore}</p>

<p><b>Информация:</b><br>
Жанр: {genre}<br>
Время: {runtime}<br>
Режиссёр: {director}<br>
Актёры: {actors}</p>

<p><b>Сборы:</b> {box_office}</p>

<p><b>Сюжет:</b><br>
{plot}</p>
"""
    return card.strip()


def convert_kinopoisk_to_omdb(kp: dict) -> dict:
    """Конвертирует данные с Кинопоиска в формат OMDB."""
    title = kp.get('nameRu') or kp.get('nameOriginal') or kp.get('nameEn') or 'Неизвестно'
    year = str(kp.get('year', 'N/A'))
    age_limits = kp.get('ratingAgeLimits', '')
    rated = age_limits.replace('age', '') + '+' if age_limits else 'N/A'
    runtime = kp.get('filmLength') or 'N/A'
    genres = kp.get('genres', [])
    genre_str = ', '.join(g['genre'].capitalize() for g in genres) if genres else 'N/A'
    plot = kp.get('description') or kp.get('shortDescription') or 'Описание отсутствует'
    poster = kp.get('posterUrl') or kp.get('posterUrlPreview') or 'N/A'

    ratings = []
    if kp.get('ratingKinopoisk'):
        ratings.append({'Source': 'Kinopoisk', 'Value': f"{kp['ratingKinopoisk']}/10"})
    if kp.get('ratingImdb'):
        ratings.append({'Source': 'Internet Movie Database', 'Value': f"{kp['ratingImdb']}/10"})
    if kp.get('ratingFilmCritics'):
        ratings.append({'Source': 'Film Critics', 'Value': f"{kp['ratingFilmCritics']}/10"})

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
    """Ищет первый фильм в выдаче Кинопоиска."""
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
        return data_id['data-id'], title
    return None


async def parse_kinopoisk(query: str) -> tuple[str | None, str | None, dict | None]:
    """Поиск фильма: Кинопоиск → fallback."""
    html = await search_kinopoisk(query)
    film_info = get_most_wanted_film_id_css(html)
    if film_info is None:
        fallback_info = await fallback_kinopoisk_get(query)
        if fallback_info[0] is None:
            return None, None, None
        film_info = fallback_info
    kinopoisk_info = await get_kinopoisk_film_info(film_info[0])
    return f'https://flcksbr.top/film/{film_info[0]}', film_info[1], convert_kinopoisk_to_omdb(kinopoisk_info)
