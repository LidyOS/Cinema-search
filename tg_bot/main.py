import asyncio
import os
from telebot.types import Message
from telebot.async_telebot import AsyncTeleBot
from load_data import MovieData
from network_requests import search_imdb
from format_card import format_movie_card, get_times_word
from format_card import parse_kinopoisk
from format_card import create_watch_button

API_KEY = os.getenv('BOT_TOKEN')

DATA_BASE = MovieData()
if API_KEY is None:
    raise RuntimeError('API_KEY is None')

BOT = AsyncTeleBot(API_KEY)

@BOT.message_handler(commands=['start'])
async def start(message: Message):
    await BOT.send_message(
        message.chat.id,
        'Привет. Это бот для поиска фильмов. Напиши название и бот постарается найти ссылку'
    )


@BOT.message_handler(commands=['help'])
async def help(message: Message):
    await BOT.send_message(
        message.chat.id,
        'Это бот для поиска фильмов. Напиши название и бот постарается найти ссылку'
    )


@BOT.message_handler(commands=['stats'])
async def help_cmd(message: Message):
    stat = DATA_BASE.select_stats_by_user(message.chat.username)

    text = "📊 <b>Статистика показов фильмов:</b>\n\n"
    for i, data in enumerate(stat):
        count = data['count(*)']
        times = get_times_word(count)

        text += f"<b>{data['original_title']}</b> — {count} {times}\n"

    await BOT.send_message(message.chat.id, text, parse_mode="HTML")

@BOT.message_handler(commands=['history'])
async def history(message: Message):
    history_data = DATA_BASE.select_queries_by_user(message.chat.username)
    text = "📜 <b>История поиска:</b>\n\n"
    for i, item in enumerate(history_data, 1):
        text += (
            f"{i}. <b>{item['original_title']}</b>\n"
            f"   🔍 Запрос: {item['query']}\n\n"
        )

    total = len(history_data)
    if total == 30:
        text += "<i>Показано последние 30 записей</i>"

    await BOT.send_message(message.chat.id, text, parse_mode="HTML")


@BOT.message_handler(content_types=["text"])
async def rememeber_all_messages(message: Message):
    user_name = message.chat.username
    if message.text and user_name:
        watch_url, original_title, kp_info = await parse_kinopoisk(message.text)
        film_info = kp_info
        if original_title:
            imdb_info = await search_imdb(original_title)
            if imdb_info is not None:
                film_info = imdb_info

        if film_info is None or original_title is None or watch_url is None:
            await BOT.send_message(
                message.chat.id,
                'По вашему запросу ничего не найдено. Попробуйте поискать другой фильм'
            )
            return

        card = format_movie_card(film_info)
        poster_url = film_info.get('Poster')
        keyboard = create_watch_button(watch_url) if watch_url else None
        await BOT.send_photo(
            chat_id=message.chat.id,
            photo=poster_url,
        )
        await BOT.send_message(message.chat.id, card, parse_mode="HTML", reply_markup=keyboard)
        DATA_BASE.add_user_query(message.text, user_name, film_info.get('Title', 'Не найдено'))

    else:
        await BOT.send_message(message.chat.id, 'Вы ввели путой запрос. Попробуйте еще раз')


if __name__ == '__main__':
    asyncio.run(BOT.polling())
