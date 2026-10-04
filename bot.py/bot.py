import discord
from discord.ext import commands
import time
from collections import defaultdict

# إعداد الصلاحيات (Intents)
intents = discord.Intents.default()
intents.members = True          # مطلوب لتتبع انضمام الأعضاء
intents.message_content = True  # مطلوب لقراءة الرسائل ومنع السبام

bot = commands.Bot(command_prefix="!", intents=intents)

# ==========================================
# 1. إعدادات نظام التحقق والتأكيد (Verification)
# ==========================================

# اسم الرتبة التي سيحصل عليها العضو بعد التحقق (تأكد من وجودها في السيرفر)
VERIFIED_ROLE_NAME = "Verified"

class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # timeout=None ليعمل الزر بشكل دائم حتى بعد إعادة تشغيل البوت

    @discord.ui.button(
        label="اضغط هنا للتحقق ✅", 
        style=discord.ButtonStyle.green, 
        custom_id="verification_button"
    )
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=VERIFIED_ROLE_NAME)
        
        if role is None:
            await interaction.response.send_message(
                f"❌ لم يتم العثور على رتبة باسم `{VERIFIED_ROLE_NAME}`! يرجى إبلاغ الإدارة.", 
                ephemeral=True
            )
            return

        if role in interaction.user.roles:
            await interaction.response.send_message(
                "✅ أنت متحقق بالفعل في السيرفر!", 
                ephemeral=True
            )
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                f"🎉 تم تأكيد حسابك ومنحك رتبة **{role.name}** بنجاح!", 
                ephemeral=True
            )

# ==========================================
# 2. حماية ضد البوتات عند الانضمام
# ==========================================

@bot.event
async def on_member_join(member: discord.Member):
    # طرد البوتات الجديدة تلقائياً
    if member.bot:
        try:
            await member.kick(reason="[حماية] يمنع دخول البوتات غير المصرح لها.")
            print(f"🛑 تم طرد البوت: {member.name}")
        except discord.Forbidden:
            print(f"⚠️ فشل طرد البوت {member.name}: البوت لا يمتلك صلاحيات كافية.")

# ==========================================
# 3. نظام منع السبام (Anti-Spam System)
# ==========================================

# سجلات تتبع الرسائل
user_messages = defaultdict(list)
SPAM_LIMIT = 5       # عدد الرسائل المسموح بها
TIME_WINDOW = 5      # خلال عدد الثواني المحدد (5 رسائل خلال 5 ثوانٍ = سبام)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    # استثناء المشرفين/الإداريين من نظام السبام
    if message.author.guild_permissions.manage_messages:
        await bot.process_commands(message)
        return

    current_time = time.time()
    user_id = message.author.id

    # مسح الرسائل القديمة خارج النطاق الزمني
    user_messages[user_id] = [t for t in user_messages[user_id] if current_time - t < TIME_WINDOW]
    user_messages[user_id].append(current_time)

    # التحقق من كسر حد السبام
    if len(user_messages[user_id]) > SPAM_LIMIT:
        try:
            await message.delete()
            await message.channel.send(
                f"⚠️ {message.author.mention} توقف عن إرسال الرسائل بشكل سريع (السبام)!", 
                delete_after=4
            )
            # اختياري: يمكنك كتم العضو مؤقتاً (Timeout) لمدة دقيقة
            # await message.author.timeout(discord.utils.utcnow() + datetime.timedelta(minutes=1), reason="Spamming")
        except discord.Forbidden:
            pass
        return

    await bot.process_commands(message)

# ==========================================
# 4. أمر لإرسال لوحة التحقق (للإدارة فقط)
# ==========================================
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    """أمر ينشئ الرسالة المزودة بزر التحقق في الروم المخصص"""
    embed = discord.Embed(
        title="🔒 نظام التحقق - Verification System",
        description="مرحباً بك في السيرفر!\nيرجى الضغط على الزر أدناه لتأكيد حسابك ودخول باقي قنوات السيرفر.",
        color=discord.Color.blue()
    )
    embed.set_footer(text="حماية السيرفر ضد الحسابات الوهمية والبوتات")
    
    await ctx.send(embed=embed, view=VerificationView())
    await ctx.message.delete()

# ==========================================
# 5. تشغيل البوت ودعم الأزرار الدائمة
# ==========================================

@bot.event
async def on_ready():
    # تسجيل الـ View لتعمل الأزرار حتى بعد إعادة تشغيل البوت
    bot.add_view(VerificationView())
    print(f"✅ تم تسجيل الدخول باسم: {bot.user.name}")
    print("🛡️ نظام الحماية والتحقق يعمل الآن بكفاءة.")

# ضع التوكن الخاص ببوتك هنا
bot.run("MTU1NTkxNDE2NDM5ODk4MTEzMA.Ga2KSt.JHvAMb81W3gu9ABGv9nbTVfScQrQq51gqkqtEw")
