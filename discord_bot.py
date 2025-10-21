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

# ------------------- Roles Mapping (Bitfield System) -------------------
ROLE_MAPPING = [
    {"flag": 1,  "role_id": 1373161181581410355}, # Owner (2^0)
    {"flag": 2,  "role_id": 1426540955762430102}, # Co-owner (2^1)
    {"flag": 4,  "role_id": 1424397304273567827}, # Developer (2^2)
    {"flag": 8,  "role_id": 1426539083823452303}, # Manager (2^3)
    {"flag": 16, "role_id": 1426538681082318848}, # Admin (2^4)
    {"flag": 32, "role_id": 1426538483035668523}, # Moderator (2^5)
]

# This creates the schema for our single integer metadata field
ROLE_METADATA = [
    {
        "key": "role_flags",
        "name": "Server Permissions",
        "description": "Verify you have the required role in the server",
        "type": 1  # 1 = integer_equal
    }
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
    """Pushes the metadata payload to Discord's API."""
    url = f"https://discord.com/api/v10/users/@me/applications/{CLIENT_ID}/role-connection"
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    payload = {"metadata": metadata}
    
    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers=headers, json=payload) as resp:
            print(f"Metadata push for user {user_id} returned status: {resp.status}")
            if resp.status != 200:
                print(f"Error pushing metadata: {await resp.text()}")
                return False # Return False on API error
            return True # Return True on success

async def push_role_metadata(user_id: int, tokens: dict):
    """Checks user roles and pushes metadata. Returns True if a badge was granted, False otherwise."""
    member_roles = await get_member_roles(user_id)
    
    role_flags = 0
    
    for mapping in ROLE_MAPPING:
        if mapping["role_id"] in member_roles:
            role_flags |= mapping["flag"]
            
    if role_flags == 0:
        # User has none of the required roles.
        print(f"❌ User {user_id} has no mapped roles. Clearing any existing badge.")
        # Pushing empty metadata removes the linked role from their profile.
        await push_metadata(user_id, tokens, {})
        return False # Return False because no role was granted
    else:
        # User has at least one role. Grant the badge.
        metadata = {
            "role_flags": role_flags
        }
        print(f"✅ Pushing metadata for user {user_id}: {metadata}")
        # Return True if the push was successful
        return await push_metadata(user_id, tokens, metadata)