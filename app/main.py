import asyncio
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import logging
from parser import parse_events
from dotenv import load_dotenv

# Установка политики цикла событий для Windows
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Основное меню
def get_main_menu():
    return ReplyKeyboardMarkup(
        [
            ["Поиск мероприятий", "Информация о боте"]
        ],
        resize_keyboard=True
    )


# Меню поиска мероприятий
def get_search_menu():
    return ReplyKeyboardMarkup(
        [
            ["Все мероприятия", "Балет"],
            ["Шоу", "Концерт"],
            ["Спектакль", "Назад"]
        ],
        resize_keyboard=True
    )


# Кнопки для события
def get_event_buttons(link):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Перейти на сайт", url=link)],
            [InlineKeyboardButton("Назад", callback_data="back_to_events")]
        ]
    )


# Функция для обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет! Я бот для поиска мероприятий в Магнитогорске. Выберите опцию:',
                                    reply_markup=get_main_menu())


# Функция для обработки нажатий на кнопки
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = update.message.text

    if user_input == "Поиск мероприятий":
        await update.message.reply_text("Выберите категорию мероприятий:", reply_markup=get_search_menu())
    elif user_input == "Информация о боте":
        await update.message.reply_text("Этот бот помогает находить мероприятия в Магнитогорске.")
    elif user_input == "Все мероприятия":
        events = parse_events('https://mgn.afishagoroda.ru/events')
        if events:
            for event in events:
                message = f"<a href='{event['link']}'>{event['title']}</a>\nЦена: {event.get('price', 'Цена не указана')}"
                if event['image_url']:
                    try:
                        await update.message.reply_photo(photo=event['image_url'], caption=message, parse_mode='HTML',
                                                         reply_markup=get_event_buttons(event['link']))
                    except Exception as e:
                        logger.error(f"Error sending photo: {e}")
                        await update.message.reply_text(message, parse_mode='HTML',
                                                        reply_markup=get_event_buttons(event['link']))
                else:
                    await update.message.reply_text(message, parse_mode='HTML',
                                                    reply_markup=get_event_buttons(event['link']))
        else:
            await update.message.reply_text("Мероприятия не найдены.")
    elif user_input == "Назад":
        await update.message.reply_text("Выберите опцию:", reply_markup=get_main_menu())
    else:
        category = user_input.lower()
        events = parse_events('https://mgn.afishagoroda.ru/events')
        filtered_events = [event for event in events if category in event['title'].lower()]
        if filtered_events:
            for event in filtered_events:
                message = f"<a href='{event['link']}'>{event['title']}</a>\nЦена: {event.get('price', 'Цена не указана')}"
                if event['image_url']:
                    try:
                        await update.message.reply_photo(photo=event['image_url'], caption=message, parse_mode='HTML',
                                                         reply_markup=get_event_buttons(event['link']))
                    except Exception as e:
                        logger.error(f"Error sending photo: {e}")
                        await update.message.reply_text(message, parse_mode='HTML',
                                                        reply_markup=get_event_buttons(event['link']))
                else:
                    await update.message.reply_text(message, parse_mode='HTML',
                                                    reply_markup=get_event_buttons(event['link']))
        else:
            await update.message.reply_text("Мероприятия не найдены.")


# Функция для обработки текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = update.message.text
    events = parse_events('https://mgn.afishagoroda.ru/events')  # Парсинг мероприятий
    filtered_events = [event for event in events if user_input.lower() in event['title'].lower()]

    if filtered_events:
        for event in filtered_events:
            message = f"<a href='{event['link']}'>{event['title']}</a>\nЦена: {event.get('price', 'Цена не указана')}"
            if event['image_url']:
                try:
                    await update.message.reply_photo(photo=event['image_url'], caption=message, parse_mode='HTML',
                                                     reply_markup=get_event_buttons(event['link']))
                except Exception as e:
                    logger.error(f"Error sending photo: {e}")
                    await update.message.reply_text(message, parse_mode='HTML',
                                                    reply_markup=get_event_buttons(event['link']))
            else:
                await update.message.reply_text(message, parse_mode='HTML',
                                                reply_markup=get_event_buttons(event['link']))
    else:
        await update.message.reply_text("Мероприятия не найдены.")


# Функция для обработки нажатий на встроенные кнопки
async def handle_inline_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "back_to_events":
        await query.edit_message_text("Выберите категорию мероприятий:", reply_markup=get_search_menu())


if __name__ == '__main__':
    load_dotenv()
    token = os.environ.get("TOKEN", "")
    application = ApplicationBuilder().token(token).connect_timeout(
        10).read_timeout(10).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_inline_button))

    application.run_polling()
