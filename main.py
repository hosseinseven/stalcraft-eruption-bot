import os
import asyncio
from datetime import datetime, timezone
from discord.ext import commands, tasks
import discord

TOKEN = os.environ.get("DISCORD_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))

intents = discord.Intents.default()  # فقط default
# intents.message_content = True  <-- این خط حذف شد

bot = commands.Bot(command_prefix="!", intents=intents)

last_eruption = datetime.now(timezone.utc)

def get_farm_status(minutes_passed):
    if minutes_passed < 15:
        return "زمان مناسب فارم ارتفیکت 🟡", 0xffd700
    elif 15 <= minutes_passed <= 30:
        return "شانس فارم خوب ✅", 0x00ff00
    else:
        return "زمان کمتر مناسب است ⚠️", 0xff0000

@tasks.loop(minutes=1)
async def simulate_eruption():
    global last_eruption
    now = datetime.now(timezone.utc)
    delta = (now - last_eruption).total_seconds() / 60
    status_text, color = get_farm_status(delta)

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        channel = await bot.fetch_channel(CHANNEL_ID)

    embed = discord.Embed(
        title="⏱️ تایمر Eruption",
        description=status_text,
        color=color
    )
    embed.add_field(
        name="آخرین Eruption",
        value=last_eruption.strftime('%Y-%m-%d %H:%M:%S UTC'),
        inline=False
    )
    embed.add_field(
        name="زمان گذشته از آخرین Eruption",
        value=f"{int(delta)} دقیقه",
        inline=False
    )

    await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    simulate_eruption.start()

async def main():
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
