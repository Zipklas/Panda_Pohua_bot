import telebot
from telebot import types
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from database import init_db, save_message
import logging
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Логи в консоль (для Docker)
        logging.FileHandler('bot.log', encoding='utf-8')  # Логи в файл
    ]
)
logger = logging.getLogger(__name__)

TOKEN = '8317300591:AAEVoa_32YGPVzAKYUjMcrfVnuDkYnBciV0'
SPOON_API_KEY = '788fb618e1274a3595b681b1459b6adf'
bot = telebot.TeleBot(TOKEN)

LIBRE_URL = "http://libretranslate:5002/translate"


def translate_to_russian(text):
    try:
        logger.info(f"Перевод текста длиной {len(text)} символов")
        payload = {
            "q": text,
            "source": "en",
            "target": "ru",
            "format": "text"
        }

        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(LIBRE_URL, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            logger.info("Перевод успешно выполнен")
            return response.json()["translatedText"]
        else:
            logger.warning(f"Ошибка перевода: статус {response.status_code}")
            return text  # если не удалось, возвращаем оригинал
    except Exception as e:
        logger.error(f"Ошибка перевода: {e}")
        return text
    
recipes_pages = {}


def send_long_text(chat_id, text, chunk_size=4000):
    """Отправляем длинный текст частями, чтобы не было ошибки Telegram"""
    logger.info(f"Отправка длинного текста в чат {chat_id}, длина: {len(text)}")
    for i in range(0, len(text), chunk_size):
        bot.send_message(chat_id, text[i:i+chunk_size])
    logger.info("Текст успешно отправлен")

def get_chinese_recipes():
    logger.info("Запрос китайских рецептов из Spoonacular API")
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {"apiKey": SPOON_API_KEY, "cuisine": "Chinese", "number": 50}
    response = requests.get(url, params=params, timeout=5).json()
    recipes_count = len(response.get("results", []))
    logger.info(f"Получено {recipes_count} рецептов")
    return response.get("results", [])

def get_recipe_detail(recipe_id, api_key):
    logger.info(f"Запрос деталей рецепта ID: {recipe_id}")
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information?apiKey={api_key}"
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Ошибка получения рецепта {recipe_id}: статус {response.status_code}")
        return "Не удалось получить рецепт.", None

    data = response.json()
    title = data.get("title", "Рецепт")
    instructions = data.get("instructions", "")
    image = data.get("image", None)

    # Убираем HTML
    soup = BeautifulSoup(instructions, "html.parser")
    instructions_clean = soup.get_text(separator="\n")

    # Переводим через LibreTranslate
    instructions_ru = translate_to_russian(instructions_clean)

    full_text = f"🍜 {title}\n\n{instructions_ru}"
    logger.info(f"Рецепт '{title}' успешно обработан")
    return full_text, image

def get_joke():
    logger.info("Запрос анекдота")
    url = "http://rzhunemogu.ru/Rand.aspx?CType=1"
    try:
        response = requests.get(url, timeout=5)
        response.encoding = 'cp1251'
        text = response.text
        start = text.find("<content>") + len("<content>")
        end = text.find("</content>")
        if start == -1 or end == -1:
            logger.warning("Не удалось найти анекдот в ответе")
            return "😔 Не удалось получить анекдот. Попробуй позже."
        joke = text[start:end].strip()
        logger.info(f"Анекдот получен, длина: {len(joke)}")
        return joke
    except Exception as e:
        logger.error(f"Ошибка получения анекдота: {e}")
        return "😔 Не удалось получить анекдот. Попробуй позже."
    

def get_story():
    logger.info("Запрос рассказа")
    url = "http://rzhunemogu.ru/Rand.aspx?CType=2"
    try:
        response = requests.get(url, timeout=5)
        response.encoding = 'cp1251'
        text = response.text
        start = text.find("<content>") + len("<content>")
        end = text.find("</content>")
        if start == -1 or end == -1:
            logger.warning("Не удалось найти рассказ в ответе")
            return "😔 Не удалось получить историю. Попробуй позже."
        story = text[start:end].strip()
        logger.info(f"Рассказ получен, длина: {len(story)}")
        return story
    except Exception as e:
        logger.error(f"Ошибка получения рассказа: {e}")
        return "😔 Не удалось получить историю. Попробуй позже."
    

#-Start
@bot.message_handler(commands=['start'])
def start(message):
    logger.info(f"Команда /start от пользователя {message.chat.id} ({message.chat.username})")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🎭 Анекдот")
    btn2 = types.KeyboardButton("📖 Рассказ")
    btn3 = types.KeyboardButton("🥡 Китайский рецепт")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id,
                     "Ахпер-джан, цавт танем! 🐼✨Я — Похуа-джан, панда не простая, а с изюминкой, как долма с имбирем! Мои шутки — острее перчика чили, а рецепты — настоены на мудрости Великого Шелкового пути и гостеприимстве армянского тоста! Говорят, в Китае любят рис, а я говорю: «Плов с соевым соусом — это джан!\nВыбери брат Джан что тебе надо:",
                     reply_markup=markup)
    logger.info("Приветственное сообщение отправлено")


@bot.message_handler(commands=['help'])
def help_command(message):
    logger.info(f"Команда /help от пользователя {message.chat.id}")
    bot.send_message(message.chat.id,
                     "Доступные команды:\n"
                     "/start - Начало работы\n"
                     "/help - Помощь\n"
                     "Или выбери категорию с клавиатуры.")
    logger.info("Справка отправлена")
    
# ------------------ Обработка ReplyKeyboard ------------------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.lower()
    chat_id = message.chat.id
    logger.info(f"Сообщение от {chat_id}: {text}")

    if text == "🎭 анекдот":
        logger.info("Запрос анекдота через кнопку")
        joke = get_joke()
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("Ещё анекдот брат Джан?", callback_data="more_joke")
        markup.add(btn)
        save_message(chat_id, f"Анекдот: {joke}")
        bot.send_message(chat_id, joke, reply_markup=markup)
        logger.info("Анекдот отправлен пользователю")

    elif text == "📖 рассказ":
        logger.info("Запрос рассказа через кнопку")
        story = get_story()
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("Ещё рассказ брат Джан?", callback_data="more_story")
        markup.add(btn)
        save_message(chat_id, f"Рассказ: {story}")
        bot.send_message(chat_id, story, reply_markup=markup)
        logger.info("Рассказ отправлен пользователю")

    elif text == "🥡 китайский рецепт":
        logger.info("Запрос китайских рецептов через кнопку")
        recipes = get_chinese_recipes()
        if not recipes:
            logger.warning("Рецепты не найдены")
            bot.send_message(chat_id, "😔 Панда не смогла найти рецепты.")
            return
        recipes_pages[chat_id] = {"recipes": recipes, "page": 0}
        logger.info(f"Создана страница рецептов для чата {chat_id}")
        send_recipe_page(chat_id)

    elif text in ["да", "ещё", "хочу ещё"]:
        logger.info(f"Пользователь {chat_id} запросил ещё контент")
        bot.send_message(chat_id, "Выбери категорию брат Джан?: 🎭 Анекдот, 📖 Рассказ или 🥡 Китайский рецепт")

    elif text in ["нет", "стоп"]:
        logger.info(f"Пользователь {chat_id} завершил сессию")
        bot.send_message(chat_id, "😄 Хорошо! Панда ждёт тебя снова!")

    else:
        logger.warning(f"Неизвестная команда от {chat_id}: {text}")
        bot.send_message(chat_id,
                         "😄 Я могу прислать анекдот брат Джан?, рассказ или рецепт. Выбери кнопку!")
        

# ------------------ Отправка страницы китайских рецептов ------------------
def send_recipe_page(chat_id):
    logger.info(f"Отправка страницы рецептов для чата {chat_id}")
    page_data = recipes_pages[chat_id]
    recipes = page_data["recipes"]
    page = page_data["page"]
    start = page * 10
    end = start + 10
    page_recipes = recipes[start:end]

    text = "🥡 Китайские рецепты:\n\n"
    markup = types.InlineKeyboardMarkup()
    
    for i, recipe in enumerate(page_recipes, start=1):
        text += f"{start+i}. {recipe['title']}\n"
        btn = types.InlineKeyboardButton(f"📖 {recipe['title']}", callback_data=f"recipe_{recipe['id']}")
        markup.add(btn)
    
    nav_buttons = []
    if end < len(recipes):
        nav_buttons.append(types.InlineKeyboardButton("➡ Следующие", callback_data="next_recipe"))
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("⬅ Назад", callback_data="prev_recipe"))
    if nav_buttons:
        markup.add(*nav_buttons)
    
    bot.send_message(chat_id, text, reply_markup=markup)
    logger.info(f"Страница {page+1} рецептов отправлена, показано {len(page_recipes)} рецептов")


# ------------------ Inline кнопки ------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    logger.info(f"Callback от {chat_id}: {call.data}")

    # 🔹 Выбор конкретного рецепта
    if call.data.startswith("recipe_"):
        recipe_id = call.data.split("_")[1]
        logger.info(f"Запрос деталей рецепта {recipe_id}")
        text, image = get_recipe_detail(recipe_id, SPOON_API_KEY)
        if image:
            bot.send_photo(chat_id, image)  # фото без подписи
            logger.info(f"Фото рецепта {recipe_id} отправлено")
        send_long_text(chat_id, text)       # текст отдельным сообщением
        save_message(chat_id, f"Номер страницы рецепта: {recipe_id}")
        logger.info(f"Текст рецепта {recipe_id} отправлен")
        
    # 🔹 Листание страниц рецептов
    elif call.data in ["next_recipe", "prev_recipe"]:
        if chat_id not in recipes_pages:
            logger.warning(f"Попытка листания без выбора рецептов: {chat_id}")
            bot.answer_callback_query(call.id, "Сначала выберите категорию 'Китайский рецепт'")
            return

        if call.data == "next_recipe":
            recipes_pages[chat_id]["page"] += 1
            logger.info(f"Следующая страница рецептов для {chat_id}")
        else:
            recipes_pages[chat_id]["page"] -= 1
            logger.info(f"Предыдущая страница рецептов для {chat_id}")

        try:
            bot.delete_message(chat_id, call.message.message_id)
            logger.info("Предыдущее сообщение с рецептами удалено")
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение: {e}")
            
        send_recipe_page(chat_id)

    # 🔹 Ещё анекдот
    elif call.data == "more_joke":
        logger.info(f"Запрос ещё анекдота от {chat_id}")
        joke = get_joke()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Ещё анекдот 😂", callback_data="more_joke"))
        save_message(chat_id, f"Анекдот: {joke}")
        bot.send_message(chat_id, joke, reply_markup=markup)
        logger.info("Дополнительный анекдот отправлен")

    # 🔹 Ещё рассказ
    elif call.data == "more_story":
        logger.info(f"Запрос ещё рассказа от {chat_id}")
        story = get_story()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Ещё рассказ 📖", callback_data="more_story"))
        save_message(chat_id, f"Рассказ: {story}")
        bot.send_message(chat_id, story, reply_markup=markup)
        logger.info("Дополнительный рассказ отправлен")

# 🔄 Запуск бота
if __name__ == "__main__":
    logger.info("Запуск бота Панда Похуа...")
    try:
        init_db()
        logger.info("База данных инициализирована")
        bot.polling(non_stop=True)
        logger.info("Бот начал работу")
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")