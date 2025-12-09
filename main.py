import discord
from discord.ext import tasks
import asyncio
from datetime import datetime, timedelta
import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# شبیه‌سازی آخرین Eruption
last_eruption = datetime.utcnow()  
eruption_interval = timedelta(hours=3)

status_messages = [
    (15, "بهترین زمان فارم Artifact 🔥"),
    (30, "شانس خوب 🎯"),
    (90, "شانس متوسط ⏳"),
]

message_obj = None

def get_status(minutes_passed):
    for limit, text in status_messages:
        if minutes_passed <= limit:
            return text
    return "اسپاون تقریباً متوقف شد – منتظر Eruption بعدی ⏱️"

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    update_timer.start()

@tasks.loop(seconds=60)
async def update_timer():
    global last_eruption, message_obj
    now = datetime.utcnow()
    minutes_passed = int((now - last_eruption).total_seconds() / 60)
    next_eruption_in = eruption_interval.total_seconds() / 60 - minutes_passed

    status_text = get_status(minutes_passed)
    embed = discord.Embed(
        title="⏳ تایمر Eruption",
        description=f"زمان گذشته از آخرین Eruption: **{minutes_passed} دقیقه**\n"
                    f"وضعیت فارم: {status_text}\n"
                    f"تا Eruption بعدی: {int(next_eruption_in)} دقیقه",
        color=0x00ff00
    )
    embed.set_footer(text="Stalcraft Eruption Timer")

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("چنل پیدا نشد")
        return

    if message_obj is None:
        message_obj = await channel.send(embed=embed)
    else:
        try:
            await message_obj.edit(embed=embed)
        except:
            message_obj = await channel.send(embed=embed)

# شبیه‌سازی خودکار Eruption جدید برای تست
@tasks.loop(seconds=eruption_interval.total_seconds())
async def simulate_eruption():
    global last_eruption
    last_eruption = datetime.utcnow()

simulate_eruption.start()
bot.run(DISCORD_TOKEN)
