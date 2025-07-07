import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from telethon import TelegramClient
from telethon.sessions import StringSession

# إعداد السجلات
logging.basicConfig(level=logging.INFO)

# توكن البوت
API_BOT_TOKEN = "7940222483:AAHwxaD1UrdCtsX8HJ-eDblAYfTKFZ3DfqA"

# تهيئة Aiogram
bot = Bot(token=API_BOT_TOKEN)
dp = Dispatcher()

# تخزين الجلسات حسب المستخدم
user_sessions = {}

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("👋 أهلاً بك! هل لديك StringSession؟\n\n✅ إذا نعم، أرسله.\n📱 إذا لا، أرسل رقم الهاتف (مثل: +2010xxxxxxx).")
    user_sessions[message.from_user.id] = {}

@dp.message(Command("reset"))
async def reset_handler(message: Message):
    user_sessions.pop(message.from_user.id, None)
    await message.answer("♻️ تم إعادة ضبط الجلسة. أرسل رقم الهاتف أو StringSession مجددًا.")

@dp.message()
async def message_handler(message: Message):
    user_id = message.from_user.id
    session = user_sessions.get(user_id)

    if not session:
        session = {}
        user_sessions[user_id] = session

    msg = message.text.strip()

    # استلام StringSession
    if "string" not in session and msg.startswith("1") and len(msg) > 100:
        session["string"] = msg
        await message.answer("✅ تم حفظ الـ StringSession. أرسل الآن API ID.")
        return

    # استلام رقم الهاتف
    if "string" not in session and "phone" not in session:
        session["phone"] = msg
        await message.answer("📞 تم حفظ رقم الهاتف. أرسل الآن API ID.")
        return

    # استلام API ID
    if "api_id" not in session:
        try:
            session["api_id"] = int(msg)
            await message.answer("🔐 تم حفظ API ID. أرسل الآن API HASH.")
        except:
            await message.answer("❌ API ID يجب أن يكون رقم.")
        return

    # استلام API HASH
    if "api_hash" not in session:
        session["api_hash"] = msg
        await message.answer("🔐 تم حفظ API HASH.")

        if "string" not in session:
            try:
                session["client"] = TelegramClient(
                    StringSession(),
                    session["api_id"],
                    session["api_hash"],
                    device_model="Samsung Galaxy S21",
                    system_version="Android 12",
                    app_version="9.4.3",
                    lang_code="en",
                    system_lang_code="en-US"
                )
                await session["client"].connect()

                if not await session["client"].is_user_authorized():
                    await session["client"].send_code_request(session["phone"])
                    await message.answer("📩 تم إرسال كود التحقق. أرسله من Telegram.")
                else:
                    string_sess = session["client"].session.save()
                    session["string"] = string_sess
                    await message.answer("✅ تم تسجيل الدخول مسبقًا.\n🔐 StringSession:\n" + string_sess + "\n\n✏️ أرسل الرسالة التي تريد نشرها.")
            except Exception as e:
                await message.answer(f"❌ فشل تسجيل الدخول:\n{e}")
        else:
            await message.answer("✏️ أرسل الرسالة التي تريد نشرها.")
        return

    # استلام كود التحقق
    if "string" not in session and "code" not in session:
        session["code"] = msg
        try:
            await session["client"].sign_in(session["phone"], session["code"])
            string_sess = session["client"].session.save()
            session["string"] = string_sess
            await message.answer("✅ تم تسجيل الدخول بنجاح.\n🔐 StringSession:\n" + string_sess + "\n\n✏️ أرسل الرسالة التي تريد نشرها.")
        except Exception as e:
            await message.answer(f"❌ فشل تسجيل الدخول بالكود:\n{e}")
        return

    # استلام نص الرسالة
    if "post_text" not in session:
        session["post_text"] = msg
        await message.answer("📥 أرسل روابط الجروبات أو القنوات (رابط في كل سطر).")
        return

    # استلام روابط الجروبات
    if "groups" not in session:
        session["groups"] = msg.splitlines()
        await message.answer("🚀 جاري بدء النشر التلقائي كل دقيقة...")
        asyncio.create_task(loop_posting(user_id))
        return

# دالة النشر لمرة واحدة
async def start_posting(user_id):
    session = user_sessions[user_id]
    text = session["post_text"]
    groups = session["groups"]

    client = TelegramClient(
        StringSession(session["string"]),
        session["api_id"],
        session["api_hash"],
        device_model="Samsung Galaxy S21",
        system_version="Android 12",
        app_version="9.4.3"
    )

    async with client:
        for group in groups:
            try:
                await client.send_message(group.strip(), text)
                await bot.send_message(user_id, f"✅ تم النشر في: {group}")
            except Exception as e:
                await bot.send_message(user_id, f"❌ فشل في: {group}\n{e}")
            await asyncio.sleep(10)

# التكرار كل دقيقة
async def loop_posting(user_id):
    try:
        while True:
            await start_posting(user_id)
            await bot.send_message(user_id, "🔁 تم تكرار النشر. سيتم النشر مرة أخرى خلال 60 ثانية...")
            await asyncio.sleep(60)
    except Exception as e:
        await bot.send_message(user_id, f"❌ حدث خطأ أثناء النشر:\n{e}")

# تشغيل البوت
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
