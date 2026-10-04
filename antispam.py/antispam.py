import discord
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()
from discord.ext import commands
from collections import defaultdict
import time
import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# تتبع رسائل الأعضاء لحساب السبام
user_messages = defaultdict(list)

# الإعدادات: (عدد الرسائل / المدة بالثواني)
SPAM_THRESHOLD = 5  # 5 رسائل
TIME_WINDOW = 5     # خلال 5 ثوانٍ
TIMEOUT_DURATION = 10 # مدة التايم أوت بالدقائق

@bot.event
async def on_ready():
    print(f"🛡️ بوت الحماية وإعطاء التايم أوت يعمل الآن باسم: {bot.user.name}")

@bot.event
async def on_message(message):
    # تجاهل الرسائل الصادرة من البوتات أو في الخاص
    if message.author.bot or not message.guild:
        return

    # صاحب السيرفر لا يمكن إعطاؤه تايم أوت
    if message.author.id == message.guild.owner_id:
        await bot.process_commands(message)
        return

    user_id = message.author.id
    current_time = time.time()

    # تنظيف الرسائل القديمة
    user_messages[user_id] = [t for t in user_messages[user_id] if current_time - t < TIME_WINDOW]
    user_messages[user_id].append(current_time)

    # 🚨 إذا تجاوز العضو حد السبام المسموح
    if len(user_messages[user_id]) >= SPAM_THRESHOLD:
        try:
            # تطبيق التايم أوت
            duration = datetime.timedelta(minutes=TIMEOUT_DURATION)
            await message.author.timeout(duration, reason="إرسال سبام ورسائل مكررة")
            
            await message.channel.send(
                f"🔇 تم إعطاء تايم أوت لـ **{message.author.mention}** لمدة {TIMEOUT_DURATION} دقائق بسبب السبام!",
                delete_after=10
            )
            user_messages[user_id].clear()
            return
        except discord.Forbidden:
            await message.channel.send("⚠️ تم اكتشاف سبام، لكن البوت لا يملك صلاحية إعطاء تايم أوت لهذا الشخص (تأكد من رفع رتبة البوت أعلاه وصلاحية Moderate Members).", delete_after=5)

    await bot.process_commands(message)

# ضع توكن بوت الحماية هنا

import os

bot.run(os.getenv("ANTISPAM_TOKEN"))
