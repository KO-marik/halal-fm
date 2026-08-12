import os
import asyncio
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
from pytgcalls.types.stream import StreamAudioEnded
import database as db

# Публичные API_ID / API_HASH от Telegram Desktop
API_ID = 2040
API_HASH = "b18441a1ed607e10e46e15600822a222"

BOT_TOKEN = os.getenv("BOT_TOKEN", "8990033747:AAEX9JsuwmkpFvpuL-KPNoexL7GgMaeExpY")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "maekiz")
PORT = int(os.getenv("PORT", 8080))

os.makedirs("tracks", exist_ok=True)

app = Client("dj_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
call_py = PyTgCalls(app)

def is_admin(_, __, query_or_msg):
    user = query_or_msg.from_user
    return user and user.username and user.username.lower() == ADMIN_USERNAME.lower()

admin_filter = filters.create(is_admin)

async def get_dj_keyboard():
    settings = await db.get_settings()
    is_loop = settings["is_loop"]
    loop_status = "🔁 Зацикливание: ВКЛ" if is_loop else "➡️ Зацикливание: ВЫКЛ"

    controls = [
        [
            InlineKeyboardButton("⏸ Пауза", callback_data="control:pause"),
            InlineKeyboardButton("▶️ Старт", callback_data="control:resume"),
            InlineKeyboardButton("⏹ Стоп", callback_data="control:stop")
        ],
        [
            InlineKeyboardButton(loop_status, callback_data="control:toggle_loop")
        ]
    ]

    tracks = await db.get_all_tracks()
    track_buttons = []
    for t in tracks:
        btn_text = f"🎵 {t['performer']} — {t['title']}"
        track_buttons.append([
            InlineKeyboardButton(btn_text, callback_data=f"play_track:{t['id']}"),
            InlineKeyboardButton("🗑", callback_data=f"del_track:{t['id']}")
        ])

    return InlineKeyboardMarkup(controls + track_buttons)

@app.on_message(filters.command("start"))
async def start_cmd(client, message: Message):
    await message.reply_text(
        "👋 Привет! Я DJ-бот.

"
        "1. Добавь меня в группу и **дай права администратора** (управление видеочатами).
"
        "2. Включи видеочат в группе.
"
        "3. Скидывай мне MP3 в ЛС и управляй эфиром через команду /dj."
    )

@app.on_message(filters.private & filters.audio & admin_filter)
async def handle_audio(client, message: Message):
    title = message.audio.title or "Без названия"
    performer = message.audio.performer or "Неизвестный исполнитель"
    file_path = os.path.join("tracks", f"{message.audio.file_unique_id}.mp3")

    msg = await message.reply_text("📥 Сохраняю трек...")
    await message.download(file_name=file_path)

    await db.add_track(title, performer, file_path)
    await msg.edit_text(
        f"✅ **Трек добавлен!**\n🎵 {performer} — {title}",
        reply_markup=await get_dj_keyboard()
    )

@app.on_message(filters.command("dj") & admin_filter)
async def dj_panel(client, message: Message):
    await message.reply_text(
        "🎛 **Панель управления эфиром @maekiz:**",
        reply_markup=await get_dj_keyboard()
    )

@app.on_callback_query(admin_filter)
async def handle_callbacks(client, callback: CallbackQuery):
    data = callback.data

    if data.startswith("play_track:"):
        track_id = int(data.split(":")[1])
        track = await db.get_track(track_id)
        chat_id = callback.message.chat.id

        if not track or not os.path.exists(track["file_path"]):
            await callback.answer("❌ Файл не найден на сервере!", show_alert=True)
            return

        try:
            try:
                await call_py.change_stream(chat_id, AudioPiped(track["file_path"]))
            except Exception:
                await call_py.join_group_call(chat_id, AudioPiped(track["file_path"]))

            await db.set_active_play(track_id, chat_id)
            await callback.answer(f"▶️ В эфире: {track['performer']} — {track['title']}")
        except Exception as e:
            await callback.answer("❌ Ошибка: Убедись, что бот — админ группы и видеочат ВКЛЮЧЕН!", show_alert=True)

    elif data == "control:toggle_loop":
        is_loop = await db.toggle_loop()
        state = "включено" if is_loop else "выключено"
        await callback.answer(f"Зацикливание {state}")
        await callback.message.edit_reply_markup(reply_markup=await get_dj_keyboard())

    elif data == "control:pause":
        await call_py.pause_stream(callback.message.chat.id)
        await callback.answer("⏸ На паузе")
    elif data == "control:resume":
        await call_py.resume_stream(callback.message.chat.id)
        await callback.answer("▶️ Возобновлено")
    elif data == "control:stop":
        await call_py.leave_group_call(callback.message.chat.id)
        await callback.answer("⏹ Эфир остановлен")

    elif data.startswith("del_track:"):
        track_id = int(data.split(":")[1])
        track = await db.get_track(track_id)
        if track:
            if os.path.exists(track["file_path"]):
                os.remove(track["file_path"])
            await db.delete_track(track_id)
            await callback.answer("Удалено")
            await callback.message.edit_reply_markup(reply_markup=await get_dj_keyboard())

@call_py.on_stream_end()
async def stream_end_handler(client, update):
    if isinstance(update, StreamAudioEnded):
        settings = await db.get_settings()
        if settings["is_loop"] and settings["current_track_id"]:
            track = await db.get_track(settings["current_track_id"])
            if track and settings["active_chat_id"]:
                await call_py.change_stream(
                    settings["active_chat_id"],
                    AudioPiped(track["file_path"])
                )

async def handle_ping(request):
    return web.Response(text="DJ Bot is running!")

async def main():
    await db.init_db()
    await app.start()
    await call_py.start()

    server = web.Server(handle_ping)
    runner = web.ServerRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()

    print("🚀 DJ Bot и Web Server запущены!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
