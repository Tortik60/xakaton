# pip install aiogram==3.*
import asyncio
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    WebAppInfo, FSInputFile, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties

# === НАСТРОЙКИ ===
BOT_TOKEN = "8294271793:AAGRzbBZMNx-slL-I51XC3SJ4GeHaqnaRPI"
WEBAPP_URL = "https://d2c7c377-dac9-449f-b86d-8457eacc908a.tunnel4.com"  # https обязателен
PHOTO_PATH = "tmk.jpg"  # положи файл рядом со скриптом

# === ИНИЦИАЛИЗАЦИЯ БОТА (aiogram 3.7+) ===
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Хранилище правильных ответов капчи: {user_id: correct_answer:int}
captcha_answers: dict[int, int] = {}


def make_captcha_kb(correct: int) -> InlineKeyboardMarkup:
    """Клавиатура с 3 вариантами + 'Другая задача'."""
    pool = set()
    while len(pool) < 2:
        delta = random.choice([-3, -2, -1, 1, 2, 3])
        fake = max(0, correct + delta)
        if fake != correct:
            pool.add(fake)
    options = [correct, *pool]
    random.shuffle(options)

    rows = [[InlineKeyboardButton(text=str(opt), callback_data=f"cap:ans:{opt}")]
            for opt in options]
    rows.append([InlineKeyboardButton(text="Другая задача", callback_data="cap:new")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def new_task():
    """Возвращает (текст вопроса, правильный ответ, клавиатуру)."""
    a, b = random.randint(2, 9), random.randint(2, 9)
    correct = a + b
    text = f"<b>Проверка входа</b>\nСколько будет <b>{a} + {b}</b>?"
    kb = make_captcha_kb(correct)
    return text, correct, kb


@dp.message(CommandStart())
async def start(m):
    # нижняя (reply) клавиатура с кнопкой "Начать"
    kb_reply = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Начать")]],
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True
    )
    await m.answer(
        "Добро пожаловать. Нажмите «Начать», чтобы пройти проверку входа.",
        reply_markup=kb_reply
    )


@dp.message(F.text)
async def on_text(m):
    # обработка нажатия нижней кнопки "Начать"
    if m.text and m.text.strip().lower() == "начать":
        # убираем нижнюю клавиатуру
        await m.answer("Запускаю проверку входа.", reply_markup=ReplyKeyboardRemove())
        # показываем капчу (инлайн-кнопки)
        text, correct, kb = new_task()
        captcha_answers[m.from_user.id] = correct
        await m.answer(text, reply_markup=kb)


@dp.callback_query(F.data.startswith("cap:"))
async def captcha_cb(c: CallbackQuery):
    user_id = c.from_user.id

    if c.data == "cap:new":
        text, correct, kb = new_task()
        captcha_answers[user_id] = correct
        await c.message.edit_text(text, reply_markup=kb)
        await c.answer("Новая задача")
        return

    if c.data.startswith("cap:ans:"):
        if user_id not in captcha_answers:
            await c.answer("Запусти /start заново.", show_alert=True)
            return

        try:
            chosen = int(c.data.split(":")[2])
        except Exception:
            await c.answer("Ошибка данных. Нажми /start.", show_alert=True)
            return

        correct = captcha_answers[user_id]
        if chosen == correct:
            captcha_answers.pop(user_id, None)

            kb_app = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Открыть магазин", web_app=WebAppInfo(url=WEBAPP_URL))]
            ])

            try:
                await c.message.edit_text("Проверка пройдена. Открывайте мини-приложение ниже.")
                await c.message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass

            try:
                photo = FSInputFile(PHOTO_PATH)
                await c.message.answer_photo(
                    photo=photo,
                    caption=(
                        "<b>Добро пожаловать в ТМК Маркетплейс.</b>\n"
                        "Здесь вы можете ознакомиться с продукцией компании ТМК, "
                        "получить актуальную информацию о наличии и условиях поставки, "
                        "а также оформить заказ напрямую через платформу."
                    ),
                    reply_markup=kb_app
                )
            except Exception:
                await c.message.answer("Не удалось отправить фото (проверь путь или размер файла).")
                await c.message.answer("Откройте мини-приложение:", reply_markup=kb_app)

            await c.answer("Верно")
        else:
            text, correct, kb = new_task()
            captcha_answers[user_id] = correct
            await c.message.edit_text("Неверно. Попробуем ещё раз.\n\n" + text, reply_markup=kb)
            await c.answer("Неверный ответ")


@dp.message(Command("shop"))
async def open_shop(m):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть магазин", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await m.answer("Откройте мини-приложение:", reply_markup=kb)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
