import discord
from discord.ext import tasks
import aiohttp
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta

# تنظیمات
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '0'))
CHECK_INTERVAL = 5  # چک کردن هر 5 ثانیه

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# متغیرهای ذخیره وضعیت
last_artifact_chance = None
last_eruption_time = None
timer_start = None


async def fetch_emission_data():
    """دریافت اطلاعات از سایت StalcraftHQ"""
    url = "https://stalcrafthq.com/emissions"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # پیدا کردن اطلاعات Last Eruption
                    eruption_text = None
                    for element in soup.find_all(string=lambda text: text and 'minutes and' in text.lower() and 'seconds ago' in text.lower()):
                        eruption_text = element.strip()
                        break
                    
                    # پیدا کردن Small Artifact Spawn Chance
                    artifact_chance = None
                    for element in soup.find_all(string=lambda text: text and 'Small Artifact Spawn Chance' in text):
                        next_sibling = element.find_next()
                        if next_sibling:
                            artifact_chance = next_sibling.get_text(strip=True)
                            break
                    
                    return {
                        'eruption': eruption_text,
                        'artifact_chance': artifact_chance
                    }
    except Exception as e:
        print(f"خطا در دریافت اطلاعات: {e}")
    
    return None


def parse_time(time_str):
    """تبدیل متن زمان به ثانیه"""
    if not time_str:
        return 0
    
    try:
        minutes = 0
        seconds = 0
        
        parts = time_str.lower().split()
        for i, part in enumerate(parts):
            if 'minute' in part and i > 0:
                minutes = int(parts[i-1])
            elif 'second' in part and i > 0:
                seconds = int(parts[i-1])
        
        return minutes * 60 + seconds
    except:
        return 0


def create_embed(data, time_remaining):
    """ساخت Embed زیبا برای پیام"""
    embed = discord.Embed(
        title="🔥 Stalcraft Emission Alert",
        description="**یک Artifact Spawn جدید شروع شده است!**",
        color=0xFF6B35,
        timestamp=datetime.utcnow()
    )
    
    # اضافه کردن فیلدها
    if data.get('eruption'):
        embed.add_field(
            name="⏱️ Last Eruption (RU)",
            value=f"`{data['eruption']}`",
            inline=False
        )
    
    if data.get('artifact_chance'):
        embed.add_field(
            name="💎 Small Artifact Spawn Chance",
            value=f"**{data['artifact_chance']}**",
            inline=False
        )
    
    # محاسبه زمان باقی‌مانده
    minutes = time_remaining // 60
    seconds = time_remaining % 60
    
    embed.add_field(
        name="⏳ زمان باقی‌مانده برای فارم",
        value=f"```{minutes:02d}:{seconds:02d}```",
        inline=False
    )
    
    embed.set_footer(text="🎮 Stalcraft Emission Tracker")
    embed.set_thumbnail(url="https://i.imgur.com/8JvZmQH.png")
    
    return embed


@tasks.loop(seconds=CHECK_INTERVAL)
async def check_emissions():
    """چک کردن تغییرات هر 5 ثانیه"""
    global last_artifact_chance, last_eruption_time, timer_start
    
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        return
    
    data = await fetch_emission_data()
    if not data:
        return
    
    current_chance = data.get('artifact_chance')
    
    # اگر Artifact Chance عوض شده بود
    if current_chance and current_chance != last_artifact_chance:
        last_artifact_chance = current_chance
        
        # محاسبه زمان
        eruption_seconds = parse_time(data.get('eruption'))
        timer_start = datetime.now()
        last_eruption_time = eruption_seconds
        
        # ارسال پیام @everyone
        embed = create_embed(data, 0)
        await channel.send("@everyone", embed=embed)
        
        print(f"✅ پیام ارسال شد - Artifact Chance جدید: {current_chance}")


@client.event
async def on_ready():
    print(f'✅ بات آماده است: {client.user}')
    print(f'📡 در حال نظارت بر کانال ID: {CHANNEL_ID}')
    
    if CHANNEL_ID == 0:
        print("⚠️ هشدار: CHANNEL_ID تنظیم نشده است!")
    
    check_emissions.start()


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    # دستور تست
    if message.content.startswith('!test'):
        data = await fetch_emission_data()
        if data:
            embed = create_embed(data, 0)
            await message.channel.send(embed=embed)
        else:
            await message.channel.send("❌ خطا در دریافت اطلاعات")


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ خطا: DISCORD_TOKEN تنظیم نشده است!")
        exit(1)
    
    client.run(DISCORD_TOKEN)
