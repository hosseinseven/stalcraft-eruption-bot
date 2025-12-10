import os
import discord
from discord.ext import tasks, commands
from datetime import datetime, timedelta

# دریافت متغیرها از محیط سیستم
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

FARM_TABLE = [
    (0, 15, "ارتفیکت عالی"),
    (15, 30, "ارتفیکت خوب"),
    (30, 45, "ارتفیکت متوسط"),
    (45, 60, "ارتفیکت پایین"),
]

@tasks.loop(minutes=1)
async def check_last_eruption():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    messages = await channel.history(limit=1).flatten()
    if not messages:
        return

    last_msg = messages[0]
    content = last_msg.content.lower()

    if "eruption" in content:
        now = datetime.utcnow()
        embed = discord.Embed(title="آخرین Eruption", description=f"زمان: {now.strftime('%H:%M:%S UTC')}", color=0x00ff00)
        for start, end, status in FARM_TABLE:
            embed.add_field(name=f"{start}-{end} دقیقه بعد", value=status, inline=False)
        await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_last_eruption.start()

bot.run(TOKEN)
