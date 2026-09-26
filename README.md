# rozimuhammadTaxi3 — Ovozli e'lonlar filtri

Ushbu bot Telegram guruh/kanallardagi **ovozli xabarlarni** tinglaydi, ularni
matnga o'giradi va taksi/pochta e'lonlariga mos kalit so'z topilsa, ovozning
o'zini (matn emas) TARGET guruhlarga, telefon raqami/profil havolasi bilan
birga yuboradi. Matnli xabarlar endi tekshirilmaydi (avvalgi versiyada
tekshirilardi) — struktura va tezlik yondashuvi bir xil qoldirilgan.

Ovozni matnga o'girish **butunlay BEPUL va OFFLINE** ishlaydi (`faster-whisper`
kutubxonasi orqali, kompyuterning o'zida) — hech qanday API kaliti, hech
qanday oylik to'lov yoki limit yo'q.

## O'rnatish

```bash
pip install -r requirements.txt
sudo apt install ffmpeg      # ovozni yaxshilash (shovqin, past/baland ovoz) uchun shart
python botTaxi.py
```

Windows'da ffmpeg: `winget install ffmpeg` (yoki qo'lda o'rnatib PATH'ga qo'shing).

Birinchi ishga tushirishda:
- Telethon telefon raqam va Telegram kodni so'raydi (bir marta).
- Whisper modeli (standart: `base`, ~140 MB) internetdan **bir martalik**
  avtomatik yuklab olinadi va kompyuterda saqlanib qoladi. Shundan keyin
  bot internetga STT uchun umuman muhtoj emas — to'liq offline ishlaydi.

`.env` fayl **shart emas** — hammasi standart sozlamalar bilan ishlayveradi.
Agar model o'lchami yoki tilni o'zgartirmoqchi bo'lsangiz: `cp .env.example .env`
va faylni tahrirlang.

## Qanday ishlaydi

1. Guruhga ovozli xabar keladi (12 daqiqagacha — undan uzunlari o'tkazib yuboriladi).
2. Ovoz yuklab olinadi va **ffmpeg** orqali tozalanadi: shovqin bosiladi,
   past chastota/shovqin kesiladi, pas gapiruvchilar kuchaytiriladi, baqirib
   gapirganlar tekislanadi — barchasi bir xil, tiniq balandlikka keltiriladi.
3. Tozalangan ovoz **kompyuterning o'zida**, `faster-whisper` orqali matnga
   o'giriladi — internetga hech narsa yuborilmaydi, hech qanday to'lov yo'q.
4. Matn `botTaxi.py` dagi **o'sha eski KEYWORDS ro'yxati** bilan solishtiriladi
   — ibora **to'liq aytilishi shart emas**: imlo xatosi, qo'shimchali so'z
   (odam → odamlar) yoki ozgina yaqin kelgan qisman ibora ham "mos" deb
   qabul qilinadi. Bu moslik **ataylab juda yumshoq** qilib qo'yilgan — asosiy
   maqsad hech qanday haqiqiy e'lonni o'tkazib yubormaslik; buning evaziga
   vaqti-vaqti bilan aloqasi yo'qroq gap ham (masalan oddiy "ketaman" so'zi)
   mos deb qabul qilinishi mumkin. Agar bunday holatlar ko'p bo'lsa,
   `MATCH_MIN_COVERAGE`ni (pastda) biroz oshiring.
5. Mos kelsa, ovozning o'zi barcha `TARGET_CHAT_IDS`ga guruh nomi, foydalanuvchi,
   telefon raqami va xabar/profil havolalari bilan birga yuboriladi.

## Tezlik

- Har bir ovozli xabar **kelgan zahoti**, boshqalarni kutmasdan, to'liq
  parallel ishlanadi — hech qanday sun'iy navbat yo'q. Bu qancha guruhga
  a'zo bo'lishingizdan (4 ta ham, 400 ta ham) mutlaqo mustaqil — guruhlar
  soni bitta xabarning ishlanish tezligiga ta'sir qilmaydi.
- Guruh/yuboruvchi ma'lumoti ovoz matnga o'girilayotgan payt bilan **parallel**
  so'raladi, shuning uchun ular kutib turmaydi.
- Bir xil ovoz (forward qilingan) ikkinchi marta qayta STTga yuborilmaydi —
  natija xotirada keshlanadi.
- STT endi **lokal** ishlagani uchun internetga borib-kelish (tarmoq
  kechikishi) ham yo'q — bu OpenAI API'ga qaraganda ko'pincha tezroq,
  ayniqsa qisqa (5-30 soniyalik) ovozlarda.
- Yagona texnik chegara — ffmpeg va Whisper protsessor yadrolari soniga
  qarab ishlaydi (`MAX_PARALLEL_FFMPEG`, `MAX_PARALLEL_WHISPER`). Bu
  operatsion tizimning tabiiy chegarasi (sun'iy "navbat" emas): agar
  bir zumda juda ko'p uzun ovoz kelib qolsa, ular CPU yadrolari sonicha
  parallel ishlanadi, undan ortig'i esa navbatga emas, shunchaki CPU
  bo'shashi bilan navbatsiz davom etadi.

## Xotira (RAM)

- Ovoz **hech qachon diskka yozilmaydi**. Yuklanadi, ffmpeg orqali tozalanadi
  va Whisper'ga uzatiladi — hammasi faqat operativ xotirada (RAM). Ishlov
  tugashi bilan (topilsa ham, topilmasa ham) o'sha bayt darhol tashlab
  yuboriladi — faqat kichkina matn (bir necha bayt) keshda qoladi, ovozning
  o'zi emas.
- **12 daqiqadan uzun** ovozli xabarlar butunlay o'tkazib yuboriladi va
  **hatto yuklab olinmaydi ham** — davomiylik Telegramning o'zi bergan
  ma'lumotdan tekshiriladi, ovozni yuklashdan oldin.

## GPU haqida

Standart holatda bot **protsessorda (CPU)** ishlaydi — bu hamma kompyuterda
ishonchli ishlaydi. Agar kuchli Nvidia videokartangiz bo'lsa, `.env` faylda
`WHISPER_DEVICE=cuda` qilib tezlashtirishingiz mumkin, lekin bunga to'liq
CUDA + cuDNN o'rnatilgan bo'lishi kerak (ko'pchilik kompyuterda bular yo'q).
Agar shunday qilib, lekin CUDA/cuDNN to'liq o'rnatilmagan bo'lsa — **xavotir
olmang**: bot xatoni ushlab, o'zi avtomatik protsessorga (CPU) o'tib,
ishlashda davom etadi, hech narsa qayta ishga tushirish shart emas.

## Sozlamalar (`botTaxi.py` boshida)

| O'zgaruvchi | Ma'nosi |
|---|---|
| `WHISPER_MODEL_SIZE` | `tiny`/`base`/`small`/`medium`/`large-v3` — chapdan o'ngga tezroq → aniqroq |
| `WHISPER_DEVICE` | `auto`/`cpu`/`cuda` |
| `WHISPER_COMPUTE_TYPE` | `int8` (CPU uchun eng tez) |
| `MATCH_MIN_COVERAGE` | 0.35 = juda yumshoq (standart, siz so'ragan holat), 0.7+ = qattiqroq |
| `FUZZY_TOKEN_SCORE` | imlo xatosini kechirish darajasi |
| `MIN_VOICE_SECONDS` / `MAX_VOICE_SECONDS` | qaysi uzunlikdagi ovozlar tekshiriladi (standart: 12 daqiqagacha) |
| `DEBUG_VOICE` | `True` bo'lsa har bir ovoz matni konsolga chiqadi |

## Kalit so'zlar (`KEYWORDS`)

Kalit so'zlar ro'yxati `botTaxi.py` faylida, avvalgidek turibdi — uni o'zingiz
tahrirlab, faqat kerakli asosiylarini qoldirsangiz bo'ladi. Ro'yxat qisqarsa,
solishtirish biroz tezlashadi (juda sezilarli emas, chunki hozir ham bitta
xabarni solishtirish millisoniyaning ulushida bajariladi) va matn ichida
tasodifiy chalkash so'zlarga tegib ketish ehtimoli kamayadi.

## .env

Ixtiyoriy. `.env.example` faylga qarang — hech narsa yozmasangiz ham standart
qiymatlar bilan ishlayveradi. `ffmpeg` esa tizimga alohida o'rnatilishi kerak
(Python paketi emas).