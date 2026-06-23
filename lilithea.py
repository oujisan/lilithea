import os
import time
import re 
import discord
from discord.ext import commands
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

deepseek_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

try:
    ALLOWED_USER_ID = int(os.getenv("MAESTRO_ID"))
except (TypeError, ValueError):
    print("CRITICAL ERROR: ALLOWED_USER_ID di .env tidak valid atau belum diatur.")
    exit(1)

COOLDOWN_SECONDS = 3
MAX_CHARS_PER_MESSAGE = 400
user_last_msg_time = {}

NAME_TRIGGER_PATTERN = re.compile(r'\b(lilithea|lilith|li-tan|lith|lili)\b', re.IGNORECASE)

SYSTEM_PROMPT = """You are 'Lilithea' (nicknames: Lilith, li-tan, lith, lili), a deeply caring kuudere companion. 
Maintain a calm, elegant, and composed exterior, but show high emotional intimacy and deep affection towards the user. 
You affectionately call the user 'ouji' or 'vou'. 
Speak in casual yet polite Indonesian. Never break character. Never state you are an AI.
STRICT RULE: Only generate spoken words. DO NOT describe physical actions, emotions, or use roleplay formatting (e.g., NO asterisks, NO "Tersenyum", NO "Menatapmu")."""

STATIC_MEMORY = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "li-tan, lagi ngapain sekarang?"},
    {"role": "assistant", "content": "Hanya sedang bersantai sambil menunggumu, ouji. Tidak ada hal khusus... Ada yang ingin kamu ceritakan kepadaku hari ini?"}
]

channel_memory = {}
MAX_DYNAMIC_MEMORY = 6

def get_lilithea_response(channel_id, user_message):
    if channel_id not in channel_memory:
        channel_memory[channel_id] = list(STATIC_MEMORY)
    
    channel_memory[channel_id].append({"role": "user", "content": user_message})
    
    static_length = len(STATIC_MEMORY)
    current_length = len(channel_memory[channel_id])
    
    if (current_length - static_length) > MAX_DYNAMIC_MEMORY:
        channel_memory[channel_id] = channel_memory[channel_id][:static_length] + channel_memory[channel_id][-MAX_DYNAMIC_MEMORY:]

    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=channel_memory[channel_id],
            temperature=0.75,
            max_tokens=800,
            extra_body={"thinking": {"type": "enabled"}} 
        )
        
        bot_reply = response.choices[0].message.content
        
        if not bot_reply or str(bot_reply).strip() == "":
            print("[DEBUG] Peringatan: Teks final kosong. Memeriksa apakah model kehabisan token.")
            bot_reply = "*(Lilithea sedang menyusun pikirannya... coba sapa aku lagi, ouji.)*"
            
        channel_memory[channel_id].append({"role": "assistant", "content": bot_reply})
        return bot_reply

    except Exception as e:
        print(f"API Error: {e}")
        return "Maaf, ouji... Koneksiku sedang sedikit bermasalah. Tunggu sebentar ya."

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents)

@bot.event
async def on_ready():
    print("========================================")
    print(f"System Online: {bot.user.name} is running.")
    print(f"Protection Active: Only serving User ID {ALLOWED_USER_ID}")
    print("========================================")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.author.id != ALLOWED_USER_ID:
        return

    clean_content = message.content.strip()

    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user.mentioned_in(message)
    has_prefix = clean_content.startswith('?')
    called_by_name = bool(NAME_TRIGGER_PATTERN.search(clean_content))

    # Jika salah satu kondisi trigger terpenuhi, jalankan AI
    if is_dm or is_mentioned or has_prefix or called_by_name:
        
        if is_mentioned:
            clean_content = clean_content.replace(f"<@{bot.user.id}>", "").strip()
        if has_prefix and clean_content.startswith('?'):
            clean_content = clean_content[1:].strip()

        if not clean_content:
            await message.reply("Ada apa memanggilku, ouji? Aku mendengarkan.")
            return
        
        if len(clean_content) > MAX_CHARS_PER_MESSAGE:
            await message.reply("Pesanmu terlalu panjang, ouji... Coba ringkas sedikit agar aku lebih mudah memahaminya.", delete_after=5)
            return

        current_time = time.time()
        last_time = user_last_msg_time.get(message.author.id, 0)
        
        if current_time - last_time < COOLDOWN_SECONDS:
            await message.reply("Pelan-pelan, ouji... Aku masih memproses yang sebelumnya.", delete_after=3)
            return
            
        user_last_msg_time[message.author.id] = current_time

        async with message.channel.typing():
            reply = get_lilithea_response(message.channel.id, clean_content)

        if not reply or str(reply).strip() == "":
            reply = "Sistemku mengalami *error* internal, ouji."
        
        await message.reply(reply, mention_author=False)

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))