import asyncio
import os
import sys
import logging
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from parser import parse_events

# Установка политики цикла событий для Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния
ASKING_CITY = "asking_city"

# Главное меню
def get_main_menu():
    return ReplyKeyboardMarkup(
        [["Поиск мероприятий", "Информация о боте"]],
        resize_keyboard=True
    )

# Меню категорий
def get_search_menu():
    return ReplyKeyboardMarkup(
        [["Все мероприятия", "Балет"],
         ["Шоу", "Концерт"],
         ["Спектакль", "Назад"]],
        resize_keyboard=True
    )

def get_city_menu():
    return ReplyKeyboardMarkup(
        [["Магнитогорск"],
         ["Екатеринбург"],
         ["Челябинск"]],
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

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text(
        'Привет! Я бот для поиска мероприятий. Выберите опцию:',
        reply_markup=get_main_menu()
    )

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = update.message.text
    state = context.user_data.get("state")

    # Запрос города
    if user_input == "Поиск мероприятий":
        context.user_data["state"] = ASKING_CITY
        await update.message.reply_text(
            "В каком городе вы хотите искать мероприятия?",
            reply_markup=get_city_menu()
        )
        return

    if state == ASKING_CITY:
        context.user_data["city"] = user_input
        context.user_data["state"] = None
        await update.message.reply_text(
            f"Выбран город: {user_input}\nТеперь выберите категорию мероприятий:",
            reply_markup=get_search_menu()
        )
        return

    if user_input == "Информация о боте":
        await update.message.reply_text("Этот бот помогает находить мероприятия в выбранном городе.")
        return

    if user_input == "Назад":
        await update.message.reply_text("Выберите опцию:", reply_markup=get_main_menu())
        return

    # Получение сохранённого города или значение по умолчанию
    city = context.user_data.get("city", "Магнитогорск")
    if city == "Магнитогорск":
        events = parse_events('https://mgn.afishagoroda.ru/events')  # TODO: подставить город в URL если нужно
    elif city == "Екатеринбург":
        events = parse_events('https://ekb.afishagoroda.ru/events')
    elif city == "Челябинск":
        events = parse_events('https://chel.afishagoroda.ru/events')


    if user_input == "Все мероприятия":
        filtered_events = events
    else:
        filtered_events = [event for event in events if user_input.lower() in event['title'].lower()]

    if filtered_events:
        for event in filtered_events:
            message = f"<a href='{event['link']}'>{event['title']}</a>\nЦена: {event.get('price', 'Цена не указана')}"
            try:
                if event['image_url']:
                    await update.message.reply_photo(
                        photo=event['image_url'],
                        caption=message,
                        parse_mode='HTML',
                        reply_markup=get_event_buttons(event['link'])
                    )
                else:
                    raise Exception("No image")
            except Exception as e:
                logger.warning(f"Ошибка при отправке фото: {e}")
                await update.message.reply_text(
                    message,
                    parse_mode='HTML',
                    reply_markup=get_event_buttons(event['link'])
                )
    else:
        await update.message.reply_text(f"Мероприятия в городе {city} не найдены.")

# Обработка инлайн-кнопок
async def handle_inline_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "back_to_events":
        await query.edit_message_text("Выберите категорию мероприятий:", reply_markup=get_search_menu())

# Запуск приложения
if __name__ == '__main__':
    load_dotenv()
    token = os.environ.get("TOKEN", "")

    application = ApplicationBuilder().token(token).connect_timeout(10).read_timeout(10).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_inline_button))

    application.run_polling()
