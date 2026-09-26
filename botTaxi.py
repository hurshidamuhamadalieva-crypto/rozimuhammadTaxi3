import io
import os
import re
import time
import shutil
import asyncio
import numpy as np
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from rapidfuzz import fuzz, process
from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat, User, DocumentAttributeAudio

# =================== TELEGRAM API ===================
api_id = 36798817
api_hash = 'db578fa6633b89b3226e22fa7c14e4f9'

# sequential_updates=False -> Telethon bir nechta kelgan xabarni ketma-ket emas,
# balki bir vaqtda (parallel) qayta ishlaydi. Bu botni sezilarli tezlashtiradi,
# chunki guruhlar ko'p bo'lganda xabarlar navbatda kutib turmaydi.
client = TelegramClient(
    'taxi_session',
    api_id,
    api_hash,
    sequential_updates=False,
)

# =================== SKIP CHAT ID ===================
# Ushbu guruh/kanallardagi xabarlar hech qachon tekshirilmaydi.
SKIP_CHAT_IDS = [
    -1002963614686,
    -1003398571650
]

# =================== TARGET CHAT ID ===================
# Topilgan e'lonlar shu guruh(lar)ga yuboriladi.
TARGET_CHAT_IDS = [
    -1002963614686,
    -1003398571650
]

# =================== KALIT SO'ZLAR (LOTIN + KIRILL) ===================
# Har bir kategoriya ostida avval qo'lda yozilgan so'zlar, keyin esa
# ularning lotin->kirill (o'zbekcha-kirill) avtomatik yozilishi keladi.

# --- ODAM / KISHI / QIZ / AYOL BOR ---
KEYWORDS_BASE_ODAM_BOR = [
    '1 kishi bor', '1 kishi bor edi', '1 kishi bor ekan', '1 kishi ekan', '1 ta qiz bola bor',
    '1 ta qiz bor', '1 киши бор', '1 та қиз бола бор', '1 та қиз бор',
    '1kishi ayol kishili mashina kerak', '1kishi bor', '1kishi ekan', '1odam bor', '1ta odam bor',
    '1ta qiz bola bor', '1ta qiz bor', '1киши аёл кишили машина керак', '1та одам бор',
    '2 kishi bor edi', '2 kishi bor ekan', '2 kishi ekan', '2 kishimiz', '2 киши бор',
    '2-kishi bor', '2-ta ayolkishi bor', '2-ta kishi bor', '2-ta odam bor', '2kishi bor',
    '2kishi ekan', '2kishimiz', '2ta ayol bor', '2ta odam bor', '2та аёл бор', '2та одам бор',
    '3 kishi bor edi', '3 kishi bor ekan', '3 kishi ekan', '3 kishimiz', '3 киши бор',
    '3-kishi bor', '3-ta ayolkishi bor', '3-ta kishi bor', '3-ta odam bor', '3kishi bor',
    '3kishi ekan', '3kishimiz', '3ta odam bor', '3та одам бор', '4 kishi bor edi',
    '4 kishi bor ekan', '4 kishimiz', '4 odam bor', '4 киши бор', '4 одам бор', '4-kishi bor',
    '4-ta ayolkishi bor', '4-ta kishi bor', '4-ta odam bor', '4kishi bor', '4kishi ekan',
    '4kishimiz', '4ta odam bor', '4та одам бор', 'amirsoydan 1kishi',
    'ayol kishi bor mashina sorashyabdi', 'ayollar bor mashina kerak', 'ayollar bor moshina kerak',
    'bagdodan 1kishi bor', 'bir qiz bir bola bor', 'bitta odam bor', "bog'doddan 2kishi",
    'Chirchiqdan 1 kishi', 'chirchiqdan 1kishi', 'ertagaga qoqonga 1kishi', "farg'onaga 1kishi",
    "farg'onaga 2kishi", "farg'onaga 3kishi", "farg'onaga 4kishi", 'fargonadan 1kishi',
    'fargonaga 2kishi', 'fargonaga odam bor', "g'azalkantdan 2 kishi", "g'azalkentdan 1kishi",
    'gazalkentdan 1kishi', 'gazalkentdan 2kishi', 'ikkita odam bor', 'kampilek odam bor',
    'katta yoshli ayol bor', 'kompilek odam bor', 'komplek odam bor', 'komplekt odam bor',
    "o'zimizdan 1kishi", 'odam bor', 'odam bor 1', 'odam bor 2', 'odam bor 3', 'odam bor 4',
    'odam bor edi', 'odam bor ekan', 'odam borakan', 'odam.bor', 'odambor', 'ozimizdan 1kishi',
    'ozimizdan 2 kishi', 'Qibraydan 1 kishi', 'qiz bola bor', 'qoqondan odam bor',
    'qoqonga 1kishi', 'qoqonga odam bor', 'rishtonga 1kishi', 'rishtonga 1kishi bor',
    'rishtonga 2kishi', 'rishtonga 3kishi', 'rishtonga 4kishi', 'rishtonga bir kishi',
    'rishtonga odam bor', 'tashkentdan rishtonga odam bor', "to'rtta odam bor", 'tortta odam bor',
    'toshkenda odam bor', "toshkendan bog'dodga odam bor", "toshkendan farg'onaga odam bor",
    'Toshkenga 1kishi', 'toshkenga 1kishi bor', 'toshkentdan 1 kishi bering degan',
    'toshkentdan 1 kishi bering deganga', 'toshkentdan 2 kishi bering degan',
    'toshkentdan 2 kishi bering deganga', 'toshkentdan 3 kishi bering degan',
    'toshkentdan 3 kishi bering deganga', 'toshkentdan 4 kishi bering degan',
    'toshkentdan 4 kishi bering deganga', 'toshkentdan bagdodga odam bor', 'toshkentdan bir kishi',
    'Toshkentdan Rishtonga 1odam bor', 'toshkentga 1kishi', 'toshkentga 1kishi bor',
    'Toshkentga 1ta odam bor', 'toshkentga 2kishi', 'toshkentga 3kishi', 'toshkentga 4kishi',
    'toshkentga odam bor', 'toshketga 1kishi', 'towga 1kishi', 'towga 2kishi', 'towga 3kishi',
    'towga 4kishi', 'uchkoprikda 1kishi', 'uchkoprikdan 1kishi', 'uchta odam bor',
    'yangiqorgondan 1kishi', 'Yangiyuldan 1 kishi', 'Zangiotadan 1 kishi', 'амирсойдан 1киши',
    'аёл киши бор машина сўрашяпти', 'аёллар бор машина керак', 'бағдодан 1киши бор',
    'бир қиз бир бола бор', 'битта одам бор', 'боғдоддан 2киши', 'газалкентдан 1киши',
    'газалкентдан 2киши', 'зангиотадан 1 киши', 'иккита одам бор', 'кампилек одам бор',
    'катта ёшли аёл бор', 'компилек одам бор', 'компилект odam бор', 'комплек одам бор',
    'комплект одам бор', 'одам бор', 'одам бор 1', 'одам бор 2', 'одам бор 3', 'одам бор 4',
    'одам бор эди', 'одам бор экан', 'озимиздан 1киши', 'озимиздан 2 киши', 'риштонга 1 киши',
    'риштонга одам бор', 'ташкентдан риштонга одам бор', 'тошкентга 1 киши', 'тошкентга одам бор',
    'тошкентдан бағдодга одам бор', 'тошкентдан боғдодга одам бор',
    'тошкентдан фарғонага одам бор', 'тўрта одам бор', 'тўртта одам бор', 'учкўприкда 1киши',
    'учкўприкдан 1киши', 'учта одам бор', 'фарғонага 1 киши', 'фарғонага 2киши',
    'фарғонага одам бор', 'фарғонадан 1киши', 'чирчиқдан 1 киши', 'чирчиқдан 1киши',
    'эртагага қўқонга 1киши', 'янгийўлдан 1 киши', 'янгиқўрғондан 1киши', 'ўзимиздан 1киши',
    'ғазалкентдан 1киши', 'ғазалкентдан 2 киши', 'қибрайдан 1 киши', 'қиз бола бор',
    'қўқонга 1киши', 'қўқонга одам бор', 'қўқондан одам бор', "Bitta odam Bor",
    "rishtonda bitaa odam", "Rishton dan Toshga 1ta odam bor", "pochta bor ekan", "pochta borekan",
    "pochta borakan", "bochta bor edi", "oldi mestaga odam bor", "bogdodga odam bor",
    "buvaydaga odam bor", "buvaydadan odam bor", "fargonaga 2 kishi", "toshkentdan pustoy mashina kerak",
    "toshdan 2 kishimiz", "rishtonga 3 ta odam bor", "ayollari bor mashina kerak",
    "ayol kishisi bor mashina bormi", "oldi bo'sh mashina kerak", "orqa salonga odam bor",
    "hozirga yurib turgan mashina kerak", "hozirga yuradigan moshina bormi",
]

# --- MASHINA / MOSHINA KERAK ---
KEYWORDS_BASE_MASHINA_KERAK = [
    'bagajli mashina kerak', 'bosh mashina bormi', 'bosh mashina kerak', 'jentra kerak',
    'kobalt kerak', 'mashina izlayapman', 'mashina kera', 'mashina keraa', 'mashina kerak',
    'mashina kerak edi', 'mashina kere', 'mashina kerek', 'mashina topaman', 'moshina kerak',
    'pustoy mashina kerak', 'yengil mashina kerak', 'багажли машина керак', 'бош машина борми',
    'бош машина керак', 'джентра керак', 'енгил машина керак', 'машина бор', 'машина излаяпман',
    'машина керeк', 'машина керак', 'машина кере', 'мошина керак', 'пустой машина керак',
]

# --- POCHTA / DOSTAVKA ---
KEYWORDS_BASE_POCHTA_DOSTAVKA = [
    'dastafka', 'dastafka bor', 'dastavka bor', 'dostavka bor', 'pochta bor', 'pochta bormi',
    'pochta kerak', 'pochta ketadi', 'pochta olib ketadi', 'даставка бор', 'доставка бор',
    'почта бор', 'почта керак', 'почта кетади', 'почта олиб кет', 'почта олиб кетади', 'пошта бор',
    'риштонга почта бор', 'риштондан почта бор', 'тошкентга почта бор', 'тошкентдан почта бор',
]

# --- KETADI / KETMOQCHI ---
KEYWORDS_BASE_KETADI_BOSHQA = [
    'bagdodga ketishi kerak', 'ketadi', 'ketishi kerak', 'ketvotti', 'toshkentga ketaman',
    'бағдодга кетиши керак', 'кетади', 'кетвотти', 'кетиши керак', 'тошкентга кетаман',
]

# --- BOSHQA KALIT SO'ZLAR ---
KEYWORDS_BASE_BOSHQA = [
    '1 kiwi bor edi', '1 kiwi bor ekan', '1 ta kamlarga', '1ta kamla', '1ta kamlarga',
    '2 kiwi bor edi', '2 kiwi bor ekan', '2 kiwimiz', '2kiwimiz', '3 kiwi bor edi',
    '3 kiwi bor ekan', '3 kiwimiz', '3kiwimiz', '4 kiwi bor edi', '4 kiwi bor ekan', '4 kiwimiz',
    '4kiwimiz', 'bagajga yuk bor', "birinchi so'raganga", 'bitta kamlarga', 'boshi bormi',
    'fargonaga kim yuryabdi', 'kim yurapti akalar', 'kim yuryabdi', "o'zimizdan kim bor",
    'ozimizdan kim bor', 'poshta  bor', 'Rishotondan 1kiwi', 'rishotondan 1kiwi bor',
    'shopir kerak', 'srochni kim yuryabdi', 'srochni yuradigan taxi kerak',
    'toshkentdan 1 kiwi bering degan', 'toshkentdan 1 kiwi bering deganga',
    'toshkentdan 2 kiwi bering deganga', 'toshkentdan 3 kiwi bering deganga',
    'toshkentdan 4 kiwi bering deganga', 'yuk bor', 'yuradiganla bormi', 'yuradiganlar bormi',
    'yurayotganla bomi', 'yurayotganla bormi', 'yurayotganlar bomi', 'yurayotganlar bormi',
    'yurediganla bormi', 'yurediganlar bomi', 'yurediganlar bormi', 'доставкa бор',
    'доставкa керак', 'кетвотди', 'кетишади', 'кетяпт', 'ким юрапти акалар', 'ким юряпти',
    'кобальт керак', 'машina кераа', 'озимиздан ким бор', 'срочни юрадиган такси керак',
    'фарғонага ким юряпти', 'шопир керак', 'юрадиганла борми', 'юрадиганлар борми',
    'юраётганла боми', 'юраётганла борми', 'юраётганлар боми', 'юраётганлар борми',
    'юредигaнла борми', 'юредигaнлар боми', 'юредигaнлар борми', 'ўзимиздан ким бор',
]

KEYWORDS_BASE = (
    KEYWORDS_BASE_ODAM_BOR +
    KEYWORDS_BASE_MASHINA_KERAK +
    KEYWORDS_BASE_POCHTA_DOSTAVKA +
    KEYWORDS_BASE_KETADI_BOSHQA +
    KEYWORDS_BASE_BOSHQA
)
# Quyidagilar - yuqoridagi lotincha so'zlarning kirillcha (o'zbek-kirill)
# ko'rinishi, avtomatik harf-ma-harf o'giril(transliteratsiya qilin)gan va
# faqat mavjud bo'lmagan (hali ro'yxatda yo'q) so'zlargina qo'shilgan.

# --- ODAM / KISHI / QIZ / AYOL BOR — kirillcha ---
KEYWORDS_TRANSLIT_ODAM_BOR = [
    '1 киши бор еди', '1 киши бор екан', '1 киши екан', '1киши бор', '1киши екан', '1одам бор',
    '1та қиз бола бор', '1та қиз бор', '2 киши бор еди', '2 киши бор екан', '2 киши екан',
    '2 кишимиз', '2-киши бор', '2-та аёлкиши бор', '2-та киши бор', '2-та одам бор', '2киши бор',
    '2киши екан', '2кишимиз', '3 киши бор еди', '3 киши бор екан', '3 киши екан', '3 кишимиз',
    '3-киши бор', '3-та аёлкиши бор', '3-та киши бор', '3-та одам бор', '3киши бор', '3киши екан',
    '3кишимиз', '4 киши бор еди', '4 киши бор екан', '4 кишимиз', '4-киши бор', '4-та аёлкиши бор',
    '4-та киши бор', '4-та одам бор', '4киши бор', '4киши екан', '4кишимиз',
    'аёл киши бор машина сорашябди', 'аёллар бор мошина керак', 'багдодан 1киши бор',
    'ертагага қоқонга 1киши', 'одам бор еди', 'одам бор екан', 'одам боракан', 'одам.бор',
    'одамбор', 'риштонга 1киши', 'риштонга 1киши бор', 'риштонга 2киши', 'риштонга 3киши',
    'риштонга 4киши', 'риштонга бир киши', 'тоwга 1киши', 'тоwга 2киши', 'тоwга 3киши',
    'тоwга 4киши', 'тортта одам бор', 'тошкенга 1киши', 'тошкенга 1киши бор', 'тошкенда одам бор',
    'тошкендан боғдодга одам бор', 'тошкендан фарғонага одам бор', 'тошкентга 1киши',
    'тошкентга 1киши бор', 'тошкентга 1та одам бор', 'тошкентга 2киши', 'тошкентга 3киши',
    'тошкентга 4киши', 'тошкентдан 1 киши беринг деган', 'тошкентдан 1 киши беринг деганга',
    'тошкентдан 2 киши беринг деган', 'тошкентдан 2 киши беринг деганга',
    'тошкентдан 3 киши беринг деган', 'тошкентдан 3 киши беринг деганга',
    'тошкентдан 4 киши беринг деган', 'тошкентдан 4 киши беринг деганга',
    'тошкентдан багдодга одам бор', 'тошкентдан бир киши', 'тошкентдан риштонга 1одам бор',
    'тошкетга 1киши', 'учкоприкда 1киши', 'учкоприкдан 1киши', 'фаргонага 2киши',
    'фаргонага одам бор', 'фаргонадан 1киши', 'фарғонага 1киши', 'фарғонага 3киши',
    'фарғонага 4киши', 'янгиюлдан 1 киши', 'янгиқоргондан 1киши', 'ғазалкантдан 2 киши',
    'қоқонга 1киши', 'қоқонга одам бор', 'қоқондан одам бор',
]

# --- MASHINA / MOSHINA KERAK — kirillcha ---
KEYWORDS_TRANSLIT_MASHINA_KERAK = [
    'жентра керак', 'йенгил машина керак', 'кобалт керак', 'машина кера', 'машина кераа',
    'машина керак еди', 'машина керек', 'машина топаман',
]

# --- POCHTA / DOSTAVKA — kirillcha ---
KEYWORDS_TRANSLIT_POCHTA_DOSTAVKA = [
    'дастафка', 'дастафка бор', 'почта борми',
]

# --- KETADI / KETMOQCHI — kirillcha ---
KEYWORDS_TRANSLIT_KETADI_BOSHQA = [
    'багдодга кетиши керак',
]

# --- BOSHQA KALIT SO'ZLAR — kirillcha ---
KEYWORDS_TRANSLIT_BOSHQA = [
    '1 киwи бор еди', '1 киwи бор екан', '1 та камларга', '1та камла', '1та камларга',
    '2 киwи бор еди', '2 киwи бор екан', '2 киwимиз', '2киwимиз', '3 киwи бор еди',
    '3 киwи бор екан', '3 киwимиз', '3киwимиз', '4 киwи бор еди', '4 киwи бор екан', '4 киwимиз',
    '4киwимиз', 'багажга юк бор', 'биринчи сўраганга', 'битта камларга', 'боши борми',
    'ким юрябди', 'ришотондан 1киwи', 'ришотондан 1киwи бор', 'срочни ким юрябди',
    'срочни юрадиган тахи керак', 'тошкентдан 1 киwи беринг деган',
    'тошкентдан 1 киwи беринг деганга', 'тошкентдан 2 киwи беринг деганга',
    'тошкентдан 3 киwи беринг деганга', 'тошкентдан 4 киwи беринг деганга', 'фаргонага ким юрябди',
    'юк бор', 'юредиганла борми', 'юредиганлар боми', 'юредиганлар борми',
    "пучта бор",
]

KEYWORDS_TRANSLIT = (
    KEYWORDS_TRANSLIT_ODAM_BOR +
    KEYWORDS_TRANSLIT_MASHINA_KERAK +
    KEYWORDS_TRANSLIT_POCHTA_DOSTAVKA +
    KEYWORDS_TRANSLIT_KETADI_BOSHQA +
    KEYWORDS_TRANSLIT_BOSHQA
)

# Ikkala ro'yxatni (lotincha + kirillcha) birlashtiramiz va aniq takrorlarni olib tashlaymiz.
KEYWORDS = list(dict.fromkeys(KEYWORDS_BASE + KEYWORDS_TRANSLIT))

KEYWORDS_RE = re.compile("|".join(re.escape(k) for k in KEYWORDS), re.IGNORECASE)
# (Yuqoridagi KEYWORDS_RE matnli xabarlar uchun edi; endi ovozli xabarlar
# match_keywords() orqali, xuddi shu KEYWORDS ro'yxati asosida tekshiriladi.)

# =================== TELEFON REGEX ===================
PHONE_RE = re.compile(r'(\+?998[\d\-\s\(\)]{9,15}|9\d{8})')


def normalize_phone(raw):
    digits = re.sub(r'\D', '', raw)
    if digits.startswith('998') and len(digits) >= 12:
        return '+' + digits[:12]
    if len(digits) == 9:
        return '+998' + digits
    return None


def get_username(user):
    """Foydalanuvchi username'ini qaytaradi.

    Telegram endi bitta akkauntda bir nechta username bo'lishiga ruxsat beradi.
    Bunday hollarda eski `.username` maydoni bo'sh (None) bo'lib qolishi mumkin,
    lekin haqiqiy username `.usernames` ro'yxatida turadi. Aynan shu sabab
    ba'zida username bor bo'lsa ham bot uni "Berkitilgan" deb ko'rsatgan.
    """
    uname = getattr(user, 'username', None)
    if uname:
        return uname
    usernames = getattr(user, 'usernames', None)
    if usernames:
        for u in usernames:
            if getattr(u, 'username', None):
                return u.username
    return None


def build_message_link(chat_id, chat_username, msg_id):
    """Xabarga to'g'ridan-to'g'ri o'tadigan havolani tuzadi.

    - Ochiq (username'li) guruh/kanal bo'lsa -> https://t.me/username/msg_id
    - Yopiq (username'siz) super-guruh/kanal bo'lsa -> https://t.me/c/ID/msg_id
      (bu havola faqat shu guruh a'zosi bo'lgan akkauntlarda ochiladi)
    - Oddiy (eski turdagi, "super" bo'lmagan) guruhlarda https://t.me/... havola
      bo'lmaydi (Telegramning o'zi bermaydi) - shu sabab tg://openmessage
      ishlatiladi, bu esa telefon/kompyuterdagi Telegram ilovasida to'g'ridan-
      to'g'ri o'sha guruh va xabarni ochadi (faqat brauzerda emas, Telegram
      ilovasi orqali bosilganda ishlaydi).
    """
    if chat_username:
        return f"https://t.me/{chat_username}/{msg_id}"
    chat_id_str = str(chat_id)
    if chat_id_str.startswith('-100'):
        internal_id = chat_id_str[4:]
        return f"https://t.me/c/{internal_id}/{msg_id}"
    if chat_id < 0:
        return f"tg://openmessage?chat_id={abs(chat_id)}&message_id={msg_id}"
    return None


# =================== KESH (TEZLIK UCHUN) ===================
# Har bir xabar uchun guruh va yuboruvchi ma'lumotini qaytadan so'rab
# o'tirmaslik uchun keshlab qo'yamiz - bu botni sezilarli tezlashtiradi.
CHAT_CACHE = {}
CHAT_CACHE_TIME = {}
SENDER_CACHE = {}
SENDER_CACHE_TIME = {}
CACHE_TTL = 1800  # 30 daqiqa - shundan keyin ma'lumot qayta yangilanadi
MAX_SENDER_CACHE = 8000  # xotira shishib ketmasligi uchun chegara


async def get_chat_info(event):
    chat_id = event.chat_id
    now = time.time()
    cached = CHAT_CACHE.get(chat_id)
    if cached and now - CHAT_CACHE_TIME.get(chat_id, 0) < CACHE_TTL:
        return cached

    chat = await event.get_chat()
    info = {
        'title': getattr(chat, 'title', 'Nomaʼlum guruh'),
        'username': getattr(chat, 'username', None),
    }
    CHAT_CACHE[chat_id] = info
    CHAT_CACHE_TIME[chat_id] = now
    return info


async def get_sender_info(event):
    sender_id = event.sender_id
    if sender_id is None:
        return None

    now = time.time()
    cached = SENDER_CACHE.get(sender_id)
    if cached and now - SENDER_CACHE_TIME.get(sender_id, 0) < CACHE_TTL:
        return cached

    sender = await event.get_sender()
    if sender is None:
        return None

    if len(SENDER_CACHE) > MAX_SENDER_CACHE:
        SENDER_CACHE.clear()
        SENDER_CACHE_TIME.clear()

    info = {
        'id': sender_id,
        'is_user': isinstance(sender, User),
        'username': get_username(sender),
        'phone': getattr(sender, 'phone', None),
    }
    SENDER_CACHE[sender_id] = info
    SENDER_CACHE_TIME[sender_id] = now
    return info


# =================== OVOZLI XABAR SOZLAMALARI ===================
# Ovozli xabar matnga o'giriladi (STT), so'ng yuqoridagi kalit so'zlar bilan
# solishtiriladi. Bu yerda BEPUL, KOMPYUTERNING O'ZIDA (offline) ishlaydigan
# "faster-whisper" ishlatiladi - hech qanday to'lov, hech qanday API kaliti,
# hech qanday oylik limit yo'q. Faqat BIRINCHI marta ishga tushirilganda
# model fayli (bir necha yuz MB) avtomatik yuklab olinadi (internet kerak),
# shundan keyin butunlay offline va bepul ishlayveradi. Model fayli
# kompyuterda saqlanib qoladi (~/.cache/huggingface) - bu ovozlarni SAQLASH
# emas, oddiy dastur fayli, xuddi Wordni o'rnatgandek bir martalik ish.
load_dotenv()

# tiny / base / small / medium / large-v3 - chapdan o'ngga: TEZROQ -> ANIQROQ.
# 'base' o'zbek tilida juda zaif chiqdi (boshqa tilga o'xshab noto'g'ri
# tarjima qildi), shuning uchun standart 'small' ga oshirildi - ancha aniqroq,
# va ovozlar baribir juda qisqa (10 soniyagacha) bo'lgani uchun sezilarli
# sekinlik bermaydi.
WHISPER_MODEL_SIZE = os.getenv('WHISPER_MODEL_SIZE', 'small').strip()
# 'auto' -> agar Nvidia GPU (CUDA) bo'lsa undan, bo'lmasa protsessordan foydalanadi.
# 'cpu' - hamma joyda ishonchli ishlaydi (standart). 'auto'/'cuda' - agar
# kompyuteringizda TO'LIQ o'rnatilgan Nvidia GPU + CUDA + cuDNN bo'lsa, ancha
# tezroq bo'ladi, lekin ko'p Windows kompyuterlarda bular to'liq o'rnatilmagan
# bo'lib, xato beradi - shu sabab standart xavfsiz 'cpu' qilib qo'yilgan.
WHISPER_DEVICE = os.getenv('WHISPER_DEVICE', 'cpu').strip()
# 'int8' - protsessorda eng tez ishlaydigan rejim (aniqlikdan deyarli yutqazmaydi).
WHISPER_COMPUTE_TYPE = os.getenv('WHISPER_COMPUTE_TYPE', 'int8').strip()
# 1 = eng tez (greedy). 5 = biroz sekinroq, ancha aniqroq. Ovoz baribir juda
# qisqa (10 soniyagacha) bo'lgani uchun 5 qilib qo'yish deyarli sekinlik
# bermaydi, lekin aniqlikni sezilarli oshiradi.
WHISPER_BEAM_SIZE = int(os.getenv('WHISPER_BEAM_SIZE', '5'))
# 'uz' = o'zbekcha. Bo'sh qoldirilsa til avtomatik aniqlanadi (sekinroq).
STT_LANGUAGE = os.getenv('STT_LANGUAGE', 'uz').strip()

# Faqat joy nomlari: model o'zbekcha nomlarni to'g'ri yozishi uchun yordam.
# (Ataylab kalit so'z YO'Q - jimlikda model shu matnni takrorlab yubormasligi uchun.)
STT_PROMPT = (
    "Toshkent, Farg'ona, Rishton, Qo'qon, Bog'dod, Buvayda, Chirchiq, "
    "G'azalkent, Yangiyo'l, Zangiota, Qibray, Uchko'prik, Amirsoy."
)

MIN_VOICE_SECONDS = 1        # bundan qisqa ovozlar (bosilib qolgan tugma) o'tkazib yuboriladi
MAX_VOICE_SECONDS = 10       # 10 soniya - bundan uzun ovozlar UMUMAN YUKLAB OLINMAYDI
MAX_PARALLEL_FFMPEG = max(2, os.cpu_count() or 2)
# Bir vaqtda nechta ovoz Whisper modelida parallel ishlanishi mumkin.
# Protsessor yadrolari sonidan oshirmagan ma'qul (ko'proq qo'ysa hammasi
# sekinlashadi, chunki hammasi bitta CPU uchun kurashadi).
MAX_PARALLEL_WHISPER = max(2, os.cpu_count() or 2)

# --- HECH QANDAY NAVBAT/KUTISH YO'Q ---
# Ovoz hech qachon diskka YOZILMAYDI - yuklanadi, filtrlanadi, yuboriladi va
# darhol RAMdan chiqarib tashlanadi (hech narsa saqlab qolinmaydi). Eski
# matnli filtr qanday kutmasdan, kelgan zahoti ishlagan bo'lsa, ovozli
# xabarlar ham AYNAN shunday - kelgan zahoti, hech qanday navbatga
# turmasdan, to'liq parallel ishlanadi. Bu qancha guruh a'zosi bo'lishidan
# butunlay mustaqil - guruhlar soni (4 ta ham, 400 ta ham) har bir alohida
# ovozning ishlanish tezligiga umuman ta'sir qilmaydi, chunki har bir xabar
# kelgan zahoti, boshqalaridan mustaqil holda darhol ishga tushadi. Faqat
# ffmpeg/Whisper jarayonlari protsessor yadrolari bilan cheklanadi - bu
# operatsion tizimning o'zi CPU tugab, hammasi sekinlashib qolmasligi
# uchun zarur texnik chegara, sun'iy "navbat" emas.

# --- Moslik darajasi ---
# Kalit ibora so'zlarining og'irlik bo'yicha qancha qismi ovozda topilsa "mos" hisoblanadi.
# PASAYTIRILDI: endi ibora ozgina yaqin kelsa ham (kam qismigina aytilsa ham) qabul qilinadi.
# 0.35 = juda yumshoq (deyarli har qanday yaqinlikni oladi). 0.7+ = qattiqroq.
MATCH_MIN_COVERAGE = 0.35
# So'z imlosidagi xatoni kechirish (0-100). Past qiymat = ko'proq kechirim.
FUZZY_TOKEN_SCORE = 74
FUZZY_STRONG_SCORE = 88   # bundan yuqori o'xshashlik to'liq mos hisoblanadi (mashna ~ mashina)
FUZZY_WEIGHT = 0.8        # bundan pastlari (74-88) kuchsizroq hisoblanadi

# True bo'lsa har bir ovozning matni va vaqti konsolga chiqadi - sozlash uchun qulay.
DEBUG_VOICE = True

FFMPEG_SEM = None
WHISPER_SEM = None
WHISPER_MODEL = None   # main() ichida yuklanadi
FFMPEG_PATH = shutil.which('ffmpeg')



# =================== MATN NORMALLASHTIRISH ===================
# Lotin/kirill, o', g', q/k, x/h, w/sh, o/a kabi farqlarni tenglashtiradi.
# Kalit so'zlar ham, ovozdan chiqqan matn ham AYNAN shu funksiyadan o'tadi,
# shuning uchun "мошина керак", "moshina kerak", "mashina kerek" bir xil bo'ladi.
_CYR = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'j',
    'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
    'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts',
    'ч': 'ch', 'ш': 'sh', 'щ': 'sh', 'ъ': '', 'ь': '', 'ы': 'i', 'э': 'e', 'ю': 'yu',
    'я': 'ya', 'ў': 'o', 'қ': 'q', 'ғ': 'g', 'ҳ': 'h',
}
_APOS = str.maketrans({c: "'" for c in "ʻʼ`´‘’′"})
_NUMBER_WORDS = {
    'bir': '1', 'bita': '1', 'iki': '2', 'ikita': '2', 'uch': '3', 'uchta': '3',
    'tart': '4', 'tarta': '4', 'besh': '5',
}


def tokenize(text):
    s = text.lower().translate(_APOS)
    s = ''.join(_CYR.get(ch, ch) for ch in s)
    s = re.sub(r"([og])'", r'\1', s)          # o' -> o, g' -> g
    s = s.replace("'", '')
    s = s.replace('w', 'sh').replace('x', 'h').replace('q', 'k').replace('o', 'a')
    s = re.sub(r'(.)\1+', r'\1', s)           # kerakk -> kerak, ikki -> iki
    words = re.findall(r'[a-z]+|\d+', s)      # "1kishi" -> "1", "kishi"
    return [_NUMBER_WORDS.get(w, w) for w in words]


# =================== KALIT SO'ZLARNI TAYYORLASH ===================
# Zaif so'zlar (bor, kerak, ...) yolg'iz o'zi hech qachon "mos" bo'lmaydi.
_WEAK_RAW = [
    'bor', 'edi', 'ekan', 'bormi', 'borakan', 'kerak', 'kera', 'kere', 'kerek', 'keraa',
    'ga', 'dan', 'da', 'ta', 'deb', 'degan', 'deganga', 'bering', 'va', 'ham', 'mi',
]
_PLACE_RAW = [
    'toshkent', 'tashkent', 'tosh', 'fargona', 'rishton', 'qoqon', 'bogdod', 'bagdod',
    'buvayda', 'chirchiq', 'gazalkent', 'yangiyol', 'yangiqorgon', 'zangiota', 'qibray',
    'uchkoprik', 'amirsoy', 'andijon', 'namangan', 'margilon', 'ozimiz',
]
WEAK_TOKENS = {t for raw in _WEAK_RAW for t in tokenize(raw)}
PLACE_STEMS = tuple({t for raw in _PLACE_RAW for t in tokenize(raw)})

W_WEAK, W_PLACE, W_STRONG = 0.4, 0.6, 1.0


def token_weight(tok):
    if tok.isdigit() or tok in WEAK_TOKENS:
        return W_WEAK
    if tok.startswith(PLACE_STEMS):
        return W_PLACE
    return W_STRONG


def _build_phrase_index():
    """[(asl_ibora, [(token, og'irlik), ...], jami_og'irlik)] - lotin va kirill
    dublikatlari normallashtirilgach bitta bo'lib qoladi."""
    seen = {}
    for kw in KEYWORDS:
        toks = tokenize(kw)
        if not toks:
            continue
        key = tuple(toks)
        if key not in seen:
            items = [(t, token_weight(t)) for t in toks]
            seen[key] = (kw, items, sum(w for _, w in items))
    return list(seen.values())


PHRASES = _build_phrase_index()
ALL_TOKENS = sorted({t for _, items, _ in PHRASES for t, _ in items})


def match_keywords(text):
    """Ovozdan chiqqan matnni kalit so'zlarga solishtiradi.

    Ibora to'liq aytilishi shart emas: uning "kuchli" so'zlaridan kamida biri
    (masalan 'odam', 'mashina', 'pochta') topilib, umumiy moslik MATCH_MIN_COVERAGE
    dan oshsa - mos hisoblanadi. So'z imlosidagi xato, qo'shimcha (odamlar),
    yopishib ketgan yozuv (odambor) ham topiladi.
    Qaytaradi: (mos_keldimi, mos_kalit_ibora, ball)
    """
    words = tokenize(text)
    if not words:
        return False, None, 0.0

    wordset = set(words)
    joined = ' '.join(words)

    # hits: {token: koeffitsient}. Aniq / qo'shimchali (odamlar) / yopishgan (odambor) /
    # kesilgan (mashin) moslik = 1.0. Faqat imlo-xato (fuzzy) bo'lsa = FUZZY_WEIGHT,
    # va u yolg'iz o'zi "kuchli" hisoblanmaydi (kelaman != ketaman).
    hits = {}
    for tok in ALL_TOKENS:
        if tok in wordset:
            hits[tok] = 1.0
            continue
        if tok.isdigit():
            continue
        n = len(tok)
        if n >= 4 and tok in joined:            # odam -> odamlar, odambor
            hits[tok] = 1.0
        elif n >= 5 and any(len(w) >= 5 and tok.startswith(w) for w in words):
            hits[tok] = 1.0                     # mashina <- mashin
        elif n >= 5:
            found = process.extractOne(
                tok, words, scorer=fuzz.ratio, score_cutoff=FUZZY_TOKEN_SCORE)
            if found:
                hits[tok] = 1.0 if found[1] >= FUZZY_STRONG_SCORE else FUZZY_WEIGHT

    best_score, best_kw = 0.0, None
    for kw, items, total in PHRASES:
        got = 0.0
        strong = False
        for tok, w in items:
            f = hits.get(tok)
            if f:
                got += w * f
                if w >= W_STRONG and f >= 1.0:
                    strong = True
        if strong:
            score = got / total
            if score >= MATCH_MIN_COVERAGE and score > best_score:
                best_score, best_kw = score, kw
    return best_kw is not None, best_kw, best_score


# =================== TOVUSHNI YAXSHILASH (ffmpeg) ===================
# Bitta ffmpeg o'tishida, xotira orqali (diskka yozmasdan):
#  - 80 Hz dan pastini (shovqin, shamol, dumdum) va 7.6 kHz dan yuqorisini kesadi
#  - foniy shovqinni kamaytiradi
#  - speechnorm: past/pas ovozni kuchli kuchaytiradi (pas gapiradiganlar tiniq eshitiladi)
#  - juda past ovozni kuchaytiradi, baland/baqiriq ovozni tekislaydi (kompressor)
#  - dynaudnorm: butun yozuv bo'yicha ovoz balandligini bir xil qiladi
#  - limiter: kuchaytirilgach "chirillab" ketmasligi uchun
#  - 16 kHz mono, xom PCM (s16le) - Whisper aynan shu formatni kutadi, shuning
#    uchun oraliqda konteyner (flac/wav) kodlash-dekodlashga vaqt sarflanmaydi.
FFMPEG_AF = (
    "highpass=f=80,lowpass=f=7600,"
    "afftdn=nr=10:nf=-35,"
    "speechnorm=e=25:r=0.0001:l=1,"
    "acompressor=threshold=0.06:ratio=3:attack=5:release=80:makeup=2,"
    "dynaudnorm=f=150:g=15:p=0.95:m=30:s=3:t=0.003,"
    "alimiter=limit=0.95"
)
_ffmpeg_warned = False


async def enhance_audio(raw):
    """Ovozni tozalab, Whisper kutadigan 16kHz mono float32 massivga aylantiradi.

    Xato bo'lsa asl ovozni o'zi (tozalanmagan holda) massivga aylantirib qaytaradi -
    bot hech qachon shu sababdan to'xtamaydi.
    """
    global _ffmpeg_warned
    args_common = ['-vn', '-ar', '16000', '-ac', '1', '-f', 's16le', 'pipe:1']
    if not FFMPEG_PATH:
        if not _ffmpeg_warned:
            _ffmpeg_warned = True
            print("⚠️ ffmpeg topilmadi - ovoz yaxshilanmasdan yuboriladi. ffmpeg o'rnating!")
        return None
    try:
        async with FFMPEG_SEM:
            proc = await asyncio.create_subprocess_exec(
                FFMPEG_PATH, '-hide_banner', '-loglevel', 'error', '-nostdin',
                '-threads', '1', '-i', 'pipe:0', '-vn',
                '-af', FFMPEG_AF, '-ar', '16000', '-ac', '1', '-f', 's16le', 'pipe:1',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                out, err = await asyncio.wait_for(proc.communicate(raw), timeout=20)
            except asyncio.TimeoutError:
                proc.kill()
                raise
        if proc.returncode == 0 and out:
            # int16 -> float32 [-1, 1] - Whisper xuddi shu formatni kutadi.
            return np.frombuffer(out, dtype=np.int16).astype(np.float32) / 32768.0
        print("⚠️ ffmpeg xatosi:", (err or b'').decode('utf-8', 'ignore')[:200])
    except Exception as e:
        print("⚠️ Ovozni yaxshilashda xatolik:", repr(e))
    return None


# =================== OVOZ -> MATN (STT, BEPUL/OFFLINE) ===================
# Whisper modeli CPU/GPU'ni band qiladigan ("blocking") kutubxona, shuning
# uchun uni asyncio.to_thread orqali alohida oqimda ishga tushiramiz - shunda
# u boshqa ovozlarni parallel ishlashga to'sqinlik qilmaydi.
def _run_whisper(samples):
    segments, _info = WHISPER_MODEL.transcribe(
        samples,
        language=STT_LANGUAGE or None,
        beam_size=WHISPER_BEAM_SIZE,
        initial_prompt=STT_PROMPT,
        vad_filter=True,               # jimlik/shovqin qismlarini tashlab ketadi - tezroq va aniqroq
        vad_parameters={"min_silence_duration_ms": 500},
        condition_on_previous_text=False,  # uzun ovozda oldingi xatoni "surib" ketmaslik uchun
    )
    return "".join(seg.text for seg in segments).strip()


_GPU_ERROR_HINTS = ('cublas', 'cudnn', 'cuda', 'nvcuda', 'nvrtc')
_gpu_fallback_lock = asyncio.Lock()


async def _fallback_whisper_to_cpu():
    """GPU (CUDA/cuDNN) to'liq o'rnatilmagan bo'lsa, botni to'xtatmasdan
    avtomatik protsessorga (CPU) o'tkazadi - qayta ishga tushirish shart emas."""
    global WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE
    async with _gpu_fallback_lock:
        if WHISPER_DEVICE == 'cpu':
            return False  # allaqachon CPU edi, boshqa hech narsa qilib bo'lmaydi
        print("⚠️ GPU (CUDA/cuDNN) kompyuterda to'liq o'rnatilmagan ko'rinadi - "
              "protsessorga (CPU) avtomatik o'tilmoqda, bot to'xtamaydi...")
        WHISPER_DEVICE, WHISPER_COMPUTE_TYPE = 'cpu', 'int8'
        WHISPER_MODEL = await asyncio.to_thread(
            WhisperModel, WHISPER_MODEL_SIZE, device='cpu', compute_type='int8'
        )
        print("✅ Endi protsessorda (CPU) davom etmoqda.")
        return True


async def transcribe_audio(samples):
    if samples is None or samples.size == 0:
        return None
    try:
        async with WHISPER_SEM:
            return await asyncio.to_thread(_run_whisper, samples)
    except Exception as e:
        msg = repr(e)
        print("⚠️ STT xatolik:", msg[:200])
        if any(h in msg.lower() for h in _GPU_ERROR_HINTS):
            try:
                if await _fallback_whisper_to_cpu():
                    async with WHISPER_SEM:
                        return await asyncio.to_thread(_run_whisper, samples)
            except Exception as e2:
                print("⚠️ CPU'da qayta urinishda ham xato:", repr(e2)[:200])
        return None




# Bir xil ovoz (boshqa guruhdan forward qilingan) qayta-qayta matnga o'girilmasin:
# natija keshlanadi, xuddi shu payt kelgan nusxalar esa bitta natijani kutadi.
TRANSCRIPT_CACHE = {}
INFLIGHT = {}
MAX_TRANSCRIPT_CACHE = 3000


def get_voice_duration(voice):
    for attr in getattr(voice, 'attributes', None) or []:
        if isinstance(attr, DocumentAttributeAudio):
            return attr.duration or 0
    return 0


async def transcribe_voice(message):
    """Ovozli xabarni yuklab, yaxshilab, matnga o'giradi.
    Qaytaradi: (matn yoki None, {bosqich: soniya})"""
    voice = message.voice
    key = voice.id

    if key in TRANSCRIPT_CACHE:
        return TRANSCRIPT_CACHE[key], {'kesh': 0.0}

    waiting = INFLIGHT.get(key)
    if waiting is not None:
        return await waiting, {'kesh': 0.0}

    fut = asyncio.get_running_loop().create_future()
    INFLIGHT[key] = fut
    timings = {}
    text = None
    try:
        t = time.perf_counter()
        raw = await message.download_media(file=bytes)
        timings['yuklash'] = time.perf_counter() - t

        if raw:
            t = time.perf_counter()
            samples = await enhance_audio(raw)
            raw = None  # asl ovoz endi kerak emas - RAMdan darhol chiqarib tashlaymiz
            timings['filtr'] = time.perf_counter() - t

            t = time.perf_counter()
            text = await transcribe_audio(samples)
            samples = None  # tozalangan ovoz ham yuborilgach darhol chiqarib tashlanadi
            timings['stt'] = time.perf_counter() - t

        if text is not None:
            if len(TRANSCRIPT_CACHE) >= MAX_TRANSCRIPT_CACHE:
                TRANSCRIPT_CACHE.clear()
            TRANSCRIPT_CACHE[key] = text
    except Exception as e:
        print("⚠️ Ovozni ishlashda xatolik:", repr(e)[:200])
    finally:
        INFLIGHT.pop(key, None)
        fut.set_result(text)
    return text, timings


SPOKEN_GAP_RE = re.compile(r'(?<=\d)[\s\-]+(?=\d)')


async def send_voice_alert(message, caption):
    """Ovozning o'zini (qayta yuklamasdan, havola orqali) barcha manzillarga yuboradi."""
    async def _send(target_id):
        try:
            return await client.send_file(
                target_id, message.voice, caption=caption, parse_mode='html'
            )
        except Exception as e:
            # Kamdan-kam: fayl havolasi eskirgan bo'lsa - qayta yuklab yuboramiz.
            print("⚠️ Ovoz havola orqali ketmadi, fayl sifatida yuborilmoqda:", repr(e)[:150])
            data = await message.download_media(file=bytes)
            bio = io.BytesIO(data)
            bio.name = 'voice.ogg'
            return await client.send_file(
                target_id, bio, caption=caption, parse_mode='html', voice_note=True,
                attributes=[DocumentAttributeAudio(
                    duration=int(get_voice_duration(message.voice)), voice=True)],
            )

    await asyncio.gather(*[_send(t) for t in TARGET_CHAT_IDS])


# =================== HANDLER ===================
@client.on(events.NewMessage(incoming=True))
async def handler(event):
    info_task = None
    try:
        # 🔥 ULANGAN SESSIYA A'ZO BO'LGAN BARCHA GURUH VA KANALLAR TEKSHIRILADI
        # (shaxsiy chatlar bundan mustasno)
        if not (event.is_group or event.is_channel):
            return

        chat_id = event.chat_id
        if chat_id in SKIP_CHAT_IDS:
            return

        # 🎤 Endi faqat OVOZLI xabarlar filtrlanadi (matnli xabarlar e'tiborga olinmaydi)
        message = event.message
        voice = message.voice
        if voice is None:
            return

        duration = get_voice_duration(voice)
        if duration < MIN_VOICE_SECONDS or duration > MAX_VOICE_SECONDS:
            return

        t_start = time.perf_counter()

        # Guruh va yuboruvchi ma'lumotini ovoz matnga o'girilayotgan paytda
        # parallel olib qo'yamiz - mos kelganda kutib o'tirmaslik uchun.
        info_task = asyncio.gather(
            get_chat_info(event),
            get_sender_info(event),
            return_exceptions=True,
        )

        # Kelgan zahoti, hech qanday navbatga turmasdan ishlanadi - to'liq parallel.
        transcript, timings = await transcribe_voice(message)

        if not transcript:
            info_task.cancel()
            return

        caption_text = event.raw_text or ''
        matched, matched_kw, score = match_keywords(f"{transcript} {caption_text}")

        if DEBUG_VOICE:
            cached = CHAT_CACHE.get(chat_id)
            gname = cached['title'] if cached else chat_id
            steps = ' | '.join(f"{k} {v:.2f}s" for k, v in timings.items())
            verdict = f"✅ MOS ({score:.2f}: {matched_kw})" if matched else "— mos emas"
            print(f"🎙 [{gname}] {duration}s «{transcript[:90]}» → {verdict} "
                  f"[{steps} | jami {time.perf_counter() - t_start:.2f}s]")

        if not matched:
            info_task.cancel()
            return

        chat_info, sender_info = await info_task
        if isinstance(chat_info, Exception):
            chat_info = await get_chat_info(event)
        if isinstance(sender_info, Exception):
            sender_info = None

        group_name = chat_info['title']

        if sender_info:
            username = sender_info['username']
            owner_display = f"@{username}" if username else "Berkitilgan"

            if sender_info['is_user']:
                profile_link = f"<a href='tg://user?id={sender_info['id']}'>Profilga o'tish</a>"
            elif username:
                profile_link = f"<a href='https://t.me/{username}'>Profilga o'tish</a>"
            else:
                profile_link = None

            phone = normalize_phone(sender_info['phone']) if sender_info['phone'] else None
        else:
            # Anonim admin nomidan yozilgan xabar (guruh nomidan yuborilgan)
            post_author = getattr(message, 'post_author', None)
            owner_display = post_author if post_author else "Anonim (guruh nomidan)"
            profile_link = None
            phone = None

        if not phone:
            # Ovozda yoki izohda (caption) aytilgan/yozilgan raqam
            phone_source = SPOKEN_GAP_RE.sub('', f"{caption_text} {transcript}")
            for m in PHONE_RE.finditer(phone_source):
                phone = normalize_phone(m.group(0))
                if phone:
                    break

        phone_display = phone if phone else "Berkitilgan"

        msg_link = build_message_link(chat_id, chat_info['username'], event.id)

        lines = [
            "🔈  <b>Elon topildi!</b>",
            "",
            "🎤  <b>Elon:</b> Audio",
            "",
            f"📍  <b>Guruh:</b> {group_name}",
            "",
            f"👤  <b>User:</b> {owner_display}",
            "",
            f"📞  <b>Raqam:</b> {phone_display}",
            "",
            "_________________________",
            "",
        ]
        if msg_link:
            lines.append(f"👉 <a href='{msg_link}'>Xabarga o'tish</a>")
        if profile_link:
            lines.append(f"🙍 {profile_link}")

        caption = "\n".join(lines)

        # Ovoz barcha manzillarga bir vaqtning o'zida (parallel) yuboriladi - tezroq.
        await send_voice_alert(message, caption)
        print(f"📨 Yuborildi (audio) -> {len(TARGET_CHAT_IDS)} ta manzil "
              f"[jami {time.perf_counter() - t_start:.2f}s]")

    except Exception as e:
        if info_task is not None:
            info_task.cancel()
        print("❌ Xatolik:", e)


# =================== KESHNI ISHGA TUSHIRISHDA TO'LDIRISH ===================
async def warm_up_cache():
    """Sessiya a'zo bo'lgan barcha guruh/kanallarni oldindan keshga oladi.

    Shu tufayli birinchi mos xabar kelganda ham guruh nomini/username'ini
    qayta so'rab o'tirmay, darhol javob beradi - bu tezlikni oshiradi va
    ayni paytda barcha ulangan guruh/kanallar nazoratda ekanini kafolatlaydi.
    """
    count = 0
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        if isinstance(entity, (Channel, Chat)):
            CHAT_CACHE[dialog.id] = {
                'title': getattr(entity, 'title', 'Nomaʼlum guruh'),
                'username': getattr(entity, 'username', None),
            }
            CHAT_CACHE_TIME[dialog.id] = time.time()
            count += 1
    return count


async def cache_refresher():
    """Guruh nomi/username o'zgarishi yoki yangi guruhga qo'shilish holatlarini
    hisobga olish uchun keshni har 15 daqiqada yangilab turadi."""
    while True:
        await asyncio.sleep(900)
        try:
            count = await warm_up_cache()
            print(f"🔄 Kesh yangilandi: {count} ta guruh/kanal")
        except Exception as e:
            print("⚠️ Kesh yangilashda xatolik:", e)


# =================== START ===================
async def init_voice_engine():
    """Ovozli xabarlarni ishlash uchun kerakli narsalarni tayyorlaydi."""
    global FFMPEG_SEM, WHISPER_SEM, WHISPER_MODEL
    FFMPEG_SEM = asyncio.Semaphore(MAX_PARALLEL_FFMPEG)
    WHISPER_SEM = asyncio.Semaphore(MAX_PARALLEL_WHISPER)
    if not FFMPEG_PATH:
        print("⚠️ ffmpeg o'rnatilmagan! Ovozni yaxshilash ishlamaydi (ffmpeg o'rnating).")

    print(f"⏳ Whisper modeli ({WHISPER_MODEL_SIZE}) tayyorlanmoqda... "
          f"birinchi marta bo'lsa internetdan bir martalik yuklab olinadi, biroz kuting.")
    t = time.perf_counter()
    try:
        # Model yuklash ham "blocking" ish - alohida oqimda, bot osilib qolmasin uchun.
        WHISPER_MODEL = await asyncio.to_thread(
            WhisperModel, WHISPER_MODEL_SIZE,
            device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE,
        )
    except Exception as e:
        # Masalan GPU/CUDA topilmasa yoki compute_type mos kelmasa - protsessorga xavfsiz o'tish.
        print(f"⚠️ Whisper'ni ({WHISPER_DEVICE}/{WHISPER_COMPUTE_TYPE}) yuklab bo'lmadi: {e!r}")
        print("   Protsessorda (cpu / int8) qayta urinilmoqda...")
        WHISPER_MODEL = await asyncio.to_thread(
            WhisperModel, WHISPER_MODEL_SIZE, device='cpu', compute_type='int8'
        )
    print(f"✅ Whisper modeli tayyor ({time.perf_counter() - t:.1f}s) - endi hammasi BEPUL va OFFLINE ishlaydi.")


async def main():
    await init_voice_engine()
    await client.start()
    count = await warm_up_cache()
    print(f"🚕 Taxi bot ishga tushdi (OVOZLI xabarlar rejimi)... {count} ta guruh/kanal nazoratga olindi.")
    asyncio.create_task(cache_refresher())
    await client.run_until_disconnected()


if __name__ == '__main__':
    client.loop.run_until_complete(main())