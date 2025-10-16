# discord_bot.py
import os
import discord
import aiohttp
from dotenv import load_dotenv

load_dotenv()

# --- Load Config from .env ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID")) 
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")

# --- Bot Setup ---
intents = discord.Intents.default()
intents.members = True # REQUIRED to see member roles
bot = discord.Client(intents=intents)

# ------------------- Roles Mapping (Single Role) -------------------
# This is set up for your one required role.
ROLE_MAPPING = [
    {"key": "has_developer_role", "role_id": 1424397304273567827, "name": "Developer"},
]

# This creates the schema that Discord needs based on your mapping above
ROLE_METADATA = [
    {
        "key": role["key"],
        "name": role["name"],
        "description": f"Has the {role['name']} role in the server",
        "type": 7  # 7 = boolean_equal
    }
    for role in ROLE_MAPPING
]

# --- Core Functions ---
async def get_member_roles(user_id: int):
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print(f"❌ Guild with ID {GUILD_ID} not found.")
        return []
    member = guild.get_member(user_id)
    if not member:
        return []
    return [role.id for role in member.roles]

async def push_metadata(user_id: int, tokens: dict, metadata: dict):
    url = f"https://discord.com/api/v10/users/@me/applications/{CLIENT_ID}/role-connection"
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers=headers, json={"metadata": metadata}) as resp:
            print(f"Metadata push for user {user_id} returned status: {resp.status}")
            if resp.status != 200:
                print(f"Error pushing metadata: {await resp.text()}")

async def push_role_metadata(user_id: int, tokens: dict):
    member_roles = await get_member_roles(user_id)
    metadata = {}
    
    required_role_id = ROLE_MAPPING[0]["role_id"]
    metadata_key = ROLE_MAPPING[0]["key"]

    if required_role_id in member_roles:
        metadata[metadata_key] = 1 # True
    else:
        metadata[metadata_key] = 0 # False

    print(f"✅ Pushing metadata for user {user_id}: {metadata}")
    await push_metadata(user_id, tokens, metadata)