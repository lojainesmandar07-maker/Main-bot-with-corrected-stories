import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID") # Optional, for testing sync commands faster

if not DISCORD_TOKEN:
    raise ValueError("لا يوجد توكن بوت ديسكورد (DISCORD_TOKEN) في البيئة!")
