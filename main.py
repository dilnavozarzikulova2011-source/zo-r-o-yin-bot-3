import asyncio
import logging
import random
import sys
from os import getenv

from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
TOKEN ="9213929772:AAFJnHf2VsZYezOlwrzZDAbmkNyqq11_2ec"

dp = Dispatcher(storage=MemoryStorage())

# ==================== FSM holatlari ====================
class GameStates(StatesGroup):
    choosing_game = State()       # O'yin tanlash
    hangman_playing = State()     # So'z o'yini
    quiz_playing = State()        # Viktorina
    number_playing = State()      # Sonni topish

# ==================== SO'Z O'YINI (HANGMAN) ====================
# So'zlar bazasi — xohlagancha kengaytirish mumkin
HANGMAN_WORDS = {
    "hayvonlar": ["it", "mushuk", "ot", "sigir", "qo'y", "echki", "tovuq", "o'rdak", "quyon", "bo'ri", "tulki", "ayiq", "sher", "yo'lbars", "fil", "maymun", "delfin", "kit", "burgut", "lochin"],
    "mevalar": ["olma", "nok", "uzum", "anor", "o'rik", "shaftoli", "gilos", "qulupnay", "malina", "tarvuz", "qovun", "limon", "apelsin", "banan", "kivi", "anjir", "xurmo", "behi", "olcha", "mandarin"],
    "kasblar": ["shifokor", "o'qituvchi", "muhandis", "dasturchi", "uchuvchi", "haydovchi", "oshpaz", "tikuvchi", "dehqon", "balIQchi", "duradgor", "temirchi", "bozorchi", "sotuvchi", "quruvchi", "rassom", "bastakor", "yozuvchi", "tarjimon", "rejissyor"],
    "davlatlar": ["o'zbekiston", "turkiya", "rossiya", "xitoy", "yaponiya", "koreya", "hindiston", "misr", "fransiya", "germaniya", "italiya", "ispaniya", "braziliya", "kanada", "avstraliya", "meksika", "argentina", "indoneziya", "pokiston", "eron"],
}

def start_hangman():
    """Tasodifiy so'z va kategoriya tanlaydi."""
    category = random.choice(list(HANGMAN_WORDS.keys()))
    word = random.choice(HANGMAN_WORDS[category]).lower()
    return category, word

def display_word(word: str, guessed: set) -> str:
    """Taxmin qilingan harflarni ochib, qolganlarini * bilan ko'rsatadi."""
    return " ".join([ch if ch in guessed or ch == " " else "*" for ch in word])

# ==================== VIKTORINA (QUIZ) ====================
# Savollar bazasi — 2000+ savolga kengaytirish mumkin
QUIZ_QUESTIONS = [
    {"q": "O'zbekistonning poytaxti qaysi shahar?", "options": ["Samarqand", "Toshkent", "Buxoro", "Andijon"], "correct": 1},
    {"q": "Quyosh sistemasidagi eng katta sayyora qaysi?", "options": ["Yer", "Mars", "Yupiter", "Saturn"], "correct": 2},
    {"q": "Python dasturlash tili qaysi yilda yaratilgan?", "options": ["1989", "1991", "1995", "2000"], "correct": 1},
    {"q": "Suvning kimyoviy formulasi qanday?", "options": ["CO2", "H2O", "O2", "NaCl"], "correct": 1},
    {"q": "O'zbekiston mustaqillikka qaysi yilda erishdi?", "options": ["1989", "1990", "1991", "1992"], "correct": 2},
    {"q": "Dunyodagi eng uzun daryo qaysi?", "options": ["Amazonka", "Nil", "Yanszi", "Missisipi"], "correct": 1},
    {"q": "Telegram qaysi yilda ishga tushgan?", "options": ["2010", "2011", "2013", "2015"], "correct": 2},
    {"q": "Inson tanasidagi eng katta organ qaysi?", "options": ["Jigar", "Miya", "Teri", "O'pka"], "correct": 2},
    {"q": "1 kilobayt necha baytga teng?", "options": ["100", "1000", "1024", "2048"], "correct": 2},
    {"q": "Qaysi til eng ko'p so'zlashuvchilarga ega?", "options": ["Ingliz", "Xitoy", "Hind", "Ispan"], "correct": 1},
]

def get_random_quiz():
    return random.choice(QUIZ_QUESTIONS)

def build_quiz_keyboard(options, correct_idx):
    """Viktorina uchun inline klaviatura yaratadi."""
    buttons = []
    for i, opt in enumerate(options):
        # callback_data da to'g'ri javob indeksini yuboramiz
        buttons.append([InlineKeyboardButton(text=opt, callback_data=f"quiz:{correct_idx}:{i}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ==================== SONNI TOPISH O'YINI ====================
def start_number_game():
    """1 dan 100 gacha tasodifiy son va urinishlar sonini qaytaradi."""
    return random.randint(1, 100), 7  # 7 ta urinish

# ==================== ASOSIY MENYU ====================
def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔤 So'z o'yini"), KeyboardButton(text="🧠 Viktorina")],
            [KeyboardButton(text="🔢 Sonni topish"), KeyboardButton(text="📊 Statistikam")],
        ],
        resize_keyboard=True
    )

# ==================== HANDLERLAR ====================

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Salom, {html.bold(message.from_user.full_name)}!\n\n"
        f"🎮 <b>O'yinlar botiga xush kelibsiz!</b>\n"
        f"3 xil o'yin mavjud:\n"
        f"• 🔤 So'z o'yini (Hangman)\n"
        f"• 🧠 Viktorina\n"
        f"• 🔢 Sonni topish\n\n"
        f"Quyidagi menyudan o'yin tanlang:",
        reply_markup=main_menu_keyboard()
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 <b>Yordam</b>\n\n"
        "/start — Bosh menyu\n"
        "/play — O'yin boshlash\n"
        "/help — Yordam\n\n"
        "O'yin davomida klaviaturadagi tugmalardan foydalaning."
    )

# ---------- SO'Z O'YINI ----------
@dp.message(F.text == "🔤 So'z o'yini")
async def hangman_start(message: Message, state: FSMContext):
    category, word = start_hangman()
    await state.update_data(
        game="hangman", word=word, category=category,
        guessed=set(), wrong=set(), max_wrong=7, attempts=0
    )
    await state.set_state(GameStates.hangman_playing)
    
    display = display_word(word, set())
    await message.answer(
        f"🔤 <b>So'z o'yini</b>\n\n"
        f"Kategoriya: <i>{category}</i>\n"
        f"So'z: <code>{display}</code>\n"
        f"({len(word)} harf)\n\n"
        f"Bitta harf yuboring. {7} marta xato qilsangiz yutqazasiz.",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(GameStates.hangman_playing, F.text)
async def hangman_guess(message: Message, state: FSMContext):
    data = await state.get_data()
    word = data["word"]
    guessed = set(data["guessed"])
    wrong = set(data["wrong"])
    max_wrong = data["max_wrong"]
    
    letter = message.text.strip().lower()
    
    # Validatsiya
    if len(letter) != 1 or not letter.isalpha():
        await message.answer("Iltimos, faqat <b>bitta harf</b> yuboring!")
        return
    
    if letter in guessed or letter in wrong:
        await message.answer("Bu harfni allaqachon taxmin qildingiz!")
        return
    
    if letter in word:
        guessed.add(letter)
        remaining = set(word) - guessed
        if not remaining:
            await state.clear()
            await message.answer(
                f"🎉 <b>Tabriklaymiz!</b>\n"
                f"So'zni topdingiz: <b>{word}</b>\n\n"
                f"Yana o'ynash uchun menyudan tanlang.",
                reply_markup=main_menu_keyboard()
            )
            return
        display = display_word(word, guessed)
        await message.answer(f"✅ To'g'ri!\n\n<code>{display}</code>")
    else:
        wrong.add(letter)
        remaining_attempts = max_wrong - len(wrong)
        if remaining_attempts <= 0:
            await state.clear()
            await message.answer(
                f"💀 <b>Yutqazdingiz!</b>\n"
                f"So'z: <b>{word}</b>\n\n"
                f"Yana o'ynash uchun menyudan tanlang.",
                reply_markup=main_menu_keyboard()
            )
            return
        display = display_word(word, guessed)
        await message.answer(
            f"❌ Xato! Qolgan urinishlar: <b>{remaining_attempts}</b>\n\n"
            f"<code>{display}</code>\n"
            f"Xato harflar: {', '.join(sorted(wrong))}"
        )
    
    await state.update_data(guessed=guessed, wrong=wrong)

# ---------- VIKTORINA ----------
@dp.message(F.text == "🧠 Viktorina")
async def quiz_start(message: Message, state: FSMContext):
    q = get_random_quiz()
    await state.update_data(game="quiz", correct_idx=q["correct"])
    await state.set_state(GameStates.quiz_playing)
    
    await message.answer(
        f"🧠 <b>Viktorina</b>\n\n{q['q']}",
        reply_markup=build_quiz_keyboard(q["options"], q["correct"])
    )

@dp.callback_query(GameStates.quiz_playing, F.data.startswith("quiz:"))
async def quiz_answer(callback: CallbackQuery, state: FSMContext):
    _, correct_idx, chosen_idx = callback.data.split(":")
    correct_idx = int(correct_idx)
    chosen_idx = int(chosen_idx)
    
    await callback.message.edit_reply_markup(reply_markup=None)
    
    if chosen_idx == correct_idx:
        await callback.answer("✅ To'g'ri!", show_alert=True)
        await callback.message.answer(
            "✅ <b>To'g'ri javob!</b>\n\n"
            "Yana savol olish uchun /play yuboring yoki menyudan tanlang.",
            reply_markup=main_menu_keyboard()
        )
    else:
        await callback.answer("❌ Xato!", show_alert=True)
        await callback.message.answer(
            f"❌ <b>Xato!</b> To'g'ri javob: <b>{correct_idx + 1}-variant</b>\n\n"
            f"Yana o'ynash uchun menyudan tanlang.",
            reply_markup=main_menu_keyboard()
        )
    
    await state.clear()

# ---------- SONNI TOPISH ----------
@dp.message(F.text == "🔢 Sonni topish")
async def number_start(message: Message, state: FSMContext):
    target, max_attempts = start_number_game()
    await state.update_data(
        game="number", target=target,
        attempts=0, max_attempts=max_attempts,
        low=1, high=100
    )
    await state.set_state(GameStates.number_playing)
    
    await message.answer(
        f"🔢 <b>Sonni topish</b>\n\n"
        f"1 dan 100 gacha son o'yladim.\n"
        f"<b>{max_attempts} ta urinish</b>ingiz bor.\n\n"
        f"Birinchi taxminingizni yuboring:",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(GameStates.number_playing, F.text)
async def number_guess(message: Message, state: FSMContext):
    data = await state.get_data()
    target = data["target"]
    attempts = data["attempts"] + 1
    max_attempts = data["max_attempts"]
    low = data["low"]
    high = data["high"]
    
    try:
        guess = int(message.text.strip())
    except ValueError:
        await message.answer("Iltimos, faqat <b>son</b> yuboring!")
        return
    
    if guess < 1 or guess > 100:
        await message.answer("1 dan 100 gacha son kiriting!")
        return
    
    if guess == target:
        await state.clear()
        await message.answer(
            f"🎉 <b>Topdingiz!</b>\n"
            f"Son: <b>{target}</b>\n"
            f"Urinishlar: {attempts}\n\n"
            f"Yana o'ynash uchun menyudan tanlang.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    if attempts >= max_attempts:
        await state.clear()
        await message.answer(
            f"💀 <b>Urinishlar tugadi!</b>\n"
            f"Men o'ylagan son: <b>{target}</b>\n\n"
            f"Yana o'ynash uchun menyudan tanlang.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    # Maslahat
    if guess < target:
        hint = "⬆️ Kattaroq son"
        low = max(low, guess + 1)
    else:
        hint = "⬇️ Kichikroq son"
        high = min(high, guess - 1)
    
    await state.update_data(attempts=attempts, low=low, high=high)
    await message.answer(
        f"{hint}\n"
        f"Oraliq: <b>{low}–{high}</b>\n"
        f"Qolgan urinishlar: <b>{max_attempts - attempts}</b>"
    )

# ---------- STATISTIKA (oddiy) ----------
@dp.message(F.text == "📊 Statistikam")
async def stats(message: Message):
    await message.answer(
        "📊 <b>Statistika</b>\n\n"
        "Hozircha statistika xotira bazasida saqlanmaydi.\n"
        "Uni SQLite yoki PostgreSQL bilan kengaytirish mumkin.",
        reply_markup=main_menu_keyboard()
    )

# ---------- ASOSIY ISHGA TUSHIRISH ----------
async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())