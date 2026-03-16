import os, sys, asyncio, random, json
from datetime import datetime

# Telethon Essentials
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

# --- CONFIGURATION & DYNAMIC LOGIN SYSTEM ---
SESSION_NAME = 'bhhayankar_v18'
DB_FILE = "bhayankgar_profiles.json"
CONFIG_FILE = "bhayankar_config.json"

# Reset Command Logic
if len(sys.argv) > 1 and sys.argv[1].lower() == "reset":
    print("\n[+] Initiating Factory Reset...")
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
        print("[+] API Configuration deleted.")
    if os.path.exists(f"{SESSION_NAME}.session"):
        os.remove(f"{SESSION_NAME}.session")
        print("[+] Old session deleted.")
    print("[+] Reset Complete. Please run the script normally to enter new credentials.\n")
    sys.exit()

def get_credentials():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            return data.get("API_ID"), data.get("API_HASH")
    else:
        print("\n" + "="*40)
        print("   BHAYANKAR V18 SUPREME SETUP")
        print("="*40)
        print("[!] API Credentials not found in system.\n")
        
        while True:
            try:
                api_id_input = input(">> Enter your API_ID (Numbers only): ").strip()
                api_id = int(api_id_input)
                break
            except ValueError:
                print("[-] Error: API_ID must be a number! Try again.")
        
        api_hash = input(">> Enter your API_HASH: ").strip()
        
        with open(CONFIG_FILE, "w") as f:
            json.dump({"API_ID": api_id, "API_HASH": api_hash}, f, indent=4)
        
        print("\n[+] Credentials locked and saved successfully!")
        print("="*40 + "\n")
        return api_id, api_hash

# Fetch or ask for credentials
API_ID, API_HASH = get_credentials()

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# --- GLOBAL VARIABLES & DB ---
START_TIME = datetime.now()
SPAM_RUNNING = False
VO_SAVER_ACTIVE = True  
ECHO_LIST = set()
ORIGINAL_INFO = {'first_name': "", 'last_name': "", 'bio': "", 'dps': []}

for folder in ["downloads", "downloads/original", "downloads/profiles", "downloads/vo"]:
    if not os.path.exists(folder): os.makedirs(folder)

def load_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, "r") as f: return json.load(f)

def save_to_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

SAVED_PROFILES = load_db()

# --- HELPER FUNCTIONS ---
async def safe_edit(event, text):
    try: return await event.edit(text, parse_mode='md')
    except: pass

async def clear_current_dps():
    try:
        curr_photos = await client.get_profile_photos('me')
        if curr_photos: await client(DeletePhotosRequest(curr_photos))
    except: pass

async def backup_master():
    global ORIGINAL_INFO
    if not ORIGINAL_INFO['first_name']: 
        me = await client.get_me()
        full = await client(GetFullUserRequest(me.id))
        ORIGINAL_INFO['first_name'] = me.first_name or ""
        ORIGINAL_INFO['last_name'] = me.last_name or ""
        ORIGINAL_INFO['bio'] = full.full_user.about or ""

        photos = await client.get_profile_photos('me')
        for i, photo in enumerate(photos):
            path = await client.download_media(photo, file=f"downloads/original/dp_{i}")
            ORIGINAL_INFO['dps'].append(path)

# ==========================================================================
# ANTI-VIEW-ONCE SYSTEM
# ==========================================================================

@client.on(events.NewMessage(outgoing=True, pattern=r'\.vo (on|off)'))
async def vo_toggle(event):
    global VO_SAVER_ACTIVE
    mode = event.pattern_match.group(1).lower()
    VO_SAVER_ACTIVE = True if mode == "on" else False
    status = "🟢 ON" if VO_SAVER_ACTIVE else "🔴 OFF"
    await safe_edit(event, f"🔱 **ANTI-VIEW-ONCE:** `{status}`")
    await asyncio.sleep(2)
    await event.delete()

@client.on(events.NewMessage(incoming=True))
async def vo_capture_engine(event):
    global VO_SAVER_ACTIVE
    if not VO_SAVER_ACTIVE or not event.media: return

    is_vo = False
    if hasattr(event.media, 'ttl_seconds') and event.media.ttl_seconds:
        is_vo = True
    elif isinstance(event.media, MessageMediaPhoto) and getattr(event.media, 'video_view_once', False):
        is_vo = True

    if is_vo:
        try:
            path = await event.download_media(file="downloads/vo/")
            caption = f"🔱 **BHAYANKAR VO CAPTURE** 🔱\n👤 **From ID:** `{event.sender_id}`\n⏰ **Time:** `{datetime.now().strftime('%H:%M:%S')}`"
            await client.send_file("me", path, caption=caption)
            if os.path.exists(path): os.remove(path)
        except Exception as e:
            print(f"VO Download Error: {e}")

# ==========================================================================
# SUPREME DOT-ART SYSTEM
# ==========================================================================

DOT_DICT = {
    'A': "  🌑🌑  \n 🌑  🌑 \n 🌑🌑🌑🌑 \n 🌑  🌑 \n 🌑  🌑 ",
    'B': " 🌑🌑🌑  \n 🌑  🌑 \n 🌑🌑🌑  \n 🌑  🌑 \n 🌑🌑🌑  ",
    'C': "  🌑🌑🌑 \n 🌑    \n 🌑    \n 🌑    \n  🌑🌑🌑 ",
    'D': " 🌑🌑🌑  \n 🌑  🌑 \n 🌑  🌑 \n 🌑  🌑 \n 🌑🌑🌑  ",
    'E': " 🌑🌑🌑🌑 \n 🌑    \n 🌑🌑🌑  \n 🌑    \n 🌑🌑🌑🌑 ",
    'F': " 🌑🌑🌑🌑 \n 🌑    \n 🌑🌑🌑  \n 🌑    \n 🌑    ",
    'G': "  🌑🌑🌑 \n 🌑    \n 🌑 🌑🌑 \n 🌑  🌑 \n  🌑🌑🌑 ",
    'H': " 🌑  🌑 \n 🌑  🌑 \n 🌑🌑🌑🌑 \n 🌑  🌑 \n 🌑  🌑 ",
    'I': " 🌑🌑🌑 \n   🌑   \n   🌑   \n   🌑   \n 🌑🌑🌑 ",
    'J': "   🌑🌑 \n    🌑  \n    🌑  \n 🌑 🌑  \n  🌑🌑  ",
    'K': " 🌑  🌑 \n 🌑 🌑  \n 🌑🌑   \n 🌑 🌑  \n 🌑  🌑 ",
    'L': " 🌑    \n 🌑    \n 🌑    \n 🌑    \n 🌑🌑🌑🌑 ",
    'M': " 🌑   🌑 \n 🌑🌑 🌑🌑 \n 🌑 🌑 🌑 \n 🌑   🌑 \n 🌑   🌑 ",
    'N': " 🌑   🌑 \n 🌑🌑  🌑 \n 🌑 🌑 🌑 \n 🌑  🌑🌑 \n 🌑   🌑 ",
    'O': "  🌑🌑  \n 🌑  🌑 \n 🌑  🌑 \n 🌑  🌑 \n  🌑🌑  ",
    'P': " 🌑🌑🌑  \n 🌑  🌑 \n 🌑🌑🌑  \n 🌑    \n 🌑    ",
    'Q': "  🌑🌑  \n 🌑  🌑 \n 🌑  🌑 \n 🌑 🌑🌑 \n  🌑🌑 🌑",
    'R': " 🌑🌑🌑  \n 🌑  🌑 \n 🌑🌑🌑  \n 🌑 🌑  \n 🌑  🌑 ",
    'S': "  🌑🌑🌑 \n 🌑    \n  🌑🌑  \n    🌑 \n 🌑🌑🌑  ",
    'T': " 🌑🌑🌑🌑🌑 \n   🌑   \n   🌑   \n   🌑   \n   🌑   ",
    'U': " 🌑  🌑 \n 🌑  🌑 \n 🌑  🌑 \n 🌑  🌑 \n  🌑🌑  ",
    'V': " 🌑  🌑 \n 🌑  🌑 \n 🌑  🌑 \n  🌑🌑  \n   🌑   ",
    'W': " 🌑   🌑 \n 🌑   🌑 \n 🌑 🌑 🌑 \n 🌑🌑 🌑🌑 \n 🌑   🌑 ",
    'X': " 🌑  🌑 \n  🌑🌑  \n   🌑   \n  🌑🌑  \n 🌑  🌑 ",
    'Y': " 🌑  🌑 \n  🌑🌑  \n   🌑   \n   🌑   \n   🌑   ",
    'Z': " 🌑🌑🌑🌑 \n    🌑  \n   🌑   \n  🌑    \n 🌑🌑🌑🌑 ",
    '0': "  🌑🌑  \n 🌑  🌑 \n 🌑  🌑 \n 🌑  🌑 \n  🌑🌑  ",
    '1': "  🌑🌑  \n   🌑   \n   🌑   \n   🌑   \n 🌑🌑🌑 ",
    '2': " 🌑🌑🌑 \n    🌑 \n 🌑🌑🌑 \n 🌑    \n 🌑🌑🌑 ",
    '3': " 🌑🌑🌑 \n    🌑 \n  🌑🌑 \n    🌑 \n 🌑🌑🌑 ",
    '4': " 🌑  🌑 \n 🌑  🌑 \n 🌑🌑🌑🌑 \n    🌑 \n    🌑 ",
    '5': " 🌑🌑🌑 \n 🌑    \n 🌑🌑🌑 \n    🌑 \n 🌑🌑🌑 ",
    '6': " 🌑🌑🌑 \n 🌑    \n 🌑🌑🌑 \n 🌑  🌑 \n 🌑🌑🌑 ",
    '7': " 🌑🌑🌑 \n    🌑 \n   🌑  \n  🌑   \n 🌑    ",
    '8': " 🌑🌑🌑 \n 🌑  🌑 \n 🌑🌑🌑 \n 🌑  🌑 \n 🌑🌑🌑 ",
    '9': " 🌑🌑🌑 \n 🌑  🌑 \n 🌑🌑🌑 \n    🌑 \n 🌑🌑🌑 ",
    ' ': "      \n      \n      \n      \n      "
}

@client.on(events.NewMessage(outgoing=True, pattern=r'\.dotart (.*)'))
async def supreme_dotart(event):
    text = event.pattern_match.group(1).upper()
    result = ["", "", "", "", ""]
    
    for char in text:
        if char in DOT_DICT:
            char_pattern = DOT_DICT[char].split('\n')
            for i in range(5):
                result[i] += char_pattern[i] + "  "
        else:
            continue
            
    final_art = "\n".join(result)
    await event.edit("📡 `Mapping Neural Art...`")
    await asyncio.sleep(0.5)
    await event.edit(f"**🔱 BHAYANKAR DOT ART 🔱**\n\n`{final_art}`")

# ==========================================================================
# IDENTITY THEFT SYSTEM 
# ==========================================================================

@client.on(events.NewMessage(pattern=r'\.clone', outgoing=True))
async def clone_soul(event):
    reply = await event.get_reply_message()
    if not reply: return await safe_edit(event, "❌ `Reply to a victim to steal identity!`")

    await safe_edit(event, "📡 `Extracting Neural Data & Media Vault...`")
    await backup_master() 

    try:
        user = await client.get_entity(reply.sender_id)
        full = await client(GetFullUserRequest(user.id))

        await client(UpdateProfileRequest(first_name=user.first_name or "", last_name=user.last_name or "", about=(full.full_user.about or "")[:70]))

        await clear_current_dps()
        photos = await client.get_profile_photos(user)

        for photo in reversed(photos):
            dl_path = await client.download_media(photo, file="downloads/tmp_media")
            await client(UploadProfilePhotoRequest(file=await client.upload_file(dl_path)))
            os.remove(dl_path)

        await safe_edit(event, f"🔱 `Identity Hijacked: {user.first_name}`")
    except Exception as e:
        await safe_edit(event, f"❌ `Clone Failed: {str(e)}`")

@client.on(events.NewMessage(pattern=r'\.revert', outgoing=True))
async def revert_soul(event):
    await backup_master() 
    if not ORIGINAL_INFO['first_name']: return await safe_edit(event, "⚠️ `No Core Backup Found!`")

    frames = ["🔄 `Decrypting Original DNA...`", "🛰 `Restoring Neural Pathways...`", "✅ `Original Identity Restored.`"]
    for frame in frames:
        await safe_edit(event, frame)
        await asyncio.sleep(0.5)

    await client(UpdateProfileRequest(first_name=ORIGINAL_INFO['first_name'], last_name=ORIGINAL_INFO['last_name'], about=ORIGINAL_INFO['bio']))

    await clear_current_dps()
    for path in reversed(ORIGINAL_INFO['dps']):
        if os.path.exists(path):
            await client(UploadProfilePhotoRequest(file=await client.upload_file(path)))

# ==========================================================================
# PROFILE VAULT SYSTEM
# ==========================================================================

@client.on(events.NewMessage(pattern=r'\.saveprofile (.*)', outgoing=True))
async def save_profile(event):
    name = event.pattern_match.group(1)
    reply = await event.get_reply_message()

    await safe_edit(event, f"💾 `Archiving Profile [{name}] to Vault...`")

    if reply:
        target = await client.get_entity(reply.sender_id)
    else:
        target = await client.get_me()

    full = await client(GetFullUserRequest(target.id))

    prof_folder = f"downloads/profiles/{name}"
    if not os.path.exists(prof_folder): os.makedirs(prof_folder)

    saved_dps = []
    photos = await client.get_profile_photos(target)
    for i, photo in enumerate(photos):
        path = await client.download_media(photo, file=f"{prof_folder}/media_{i}")
        saved_dps.append(path)

    SAVED_PROFILES[name] = {
        'fn': target.first_name or "", 'ln': target.last_name or "",
        'bio': full.full_user.about or "", 'dps': saved_dps
    }
    save_to_db(SAVED_PROFILES)
    await safe_edit(event, f"✅ `Profile Vaulted: '{name}'`")

@client.on(events.NewMessage(pattern=r'\.loadprofile (.*)', outgoing=True))
async def load_profile(event):
    name = event.pattern_match.group(1)
    if name not in SAVED_PROFILES: return await safe_edit(event, f"❌ `Profile '{name}' not found in Vault!`")

    data = SAVED_PROFILES[name]
    await backup_master() 

    frames = [f"⚙️ `Accessing Vault: {name}...`", "🔄 `Deploying Stored Identity...`", f"🔱 `Active Profile: '{name}'`"]
    for frame in frames:
        await safe_edit(event, frame)
        await asyncio.sleep(0.4)

    await client(UpdateProfileRequest(first_name=data['fn'], last_name=data['ln'], about=data['bio']))

    await clear_current_dps()
    for path in reversed(data.get('dps', [])):
        if os.path.exists(path):
            await client(UploadProfilePhotoRequest(file=await client.upload_file(path)))

@client.on(events.NewMessage(pattern=r'\.delprofile (.*)', outgoing=True))
async def del_profile(event):
    name = event.pattern_match.group(1)
    if name in SAVED_PROFILES:
        del SAVED_PROFILES[name]
        save_to_db(SAVED_PROFILES)
        prof_folder = f"downloads/profiles/{name}"
        if os.path.exists(prof_folder):
            for file in os.listdir(prof_folder): os.remove(f"{prof_folder}/{file}")
            os.rmdir(prof_folder)
        await safe_edit(event, f"🗑 `Profile '{name}' erased from Vault.`")
    else:
        await safe_edit(event, "❌ `Profile not found!`")

@client.on(events.NewMessage(pattern=r'\.profiles', outgoing=True))
async def list_profiles(event):
    if not SAVED_PROFILES: return await safe_edit(event, "🗄 `Profile Vault is Empty.`")
    msg = "**🗄 ıllıllı PROFILE VAULT ıllıllı 🗄**\n\n"
    for name in SAVED_PROFILES: msg += f"• `{name}`\n"
    await safe_edit(event, msg)

# ==========================================================================
# SUPREME ATTACK SYSTEM
# ==========================================================================

@client.on(events.NewMessage(pattern=r'\.spam (\d+) ([\d\.]+) (.*)', outgoing=True))
async def custom_spam(event):
    global SPAM_RUNNING
    SPAM_RUNNING = True
    count = int(event.pattern_match.group(1))
    delay = float(event.pattern_match.group(2))
    msg = event.pattern_match.group(3)
    await event.delete()
    for _ in range(count):
        if not SPAM_RUNNING: break
        await client.send_message(event.chat_id, msg)
        await asyncio.sleep(delay)

@client.on(events.NewMessage(pattern=r'\.echo', outgoing=True))
async def echo_toggle(event):
    global ECHO_LIST
    reply = await event.get_reply_message()
    if not reply: return await safe_edit(event, "❌ `Reply to victim!`")
    uid = reply.sender_id
    ECHO_LIST.add(uid)
    await safe_edit(event, f"📣 `Echo Active on Target: {uid}`")

@client.on(events.NewMessage(pattern=r'\.unecho', outgoing=True))
async def unecho_toggle(event):
    global ECHO_LIST
    reply = await event.get_reply_message()
    if not reply: return await safe_edit(event, "❌ `Reply to victim!`")
    uid = reply.sender_id
    if uid in ECHO_LIST:
        ECHO_LIST.remove(uid)
        await safe_edit(event, f"🔕 `Echo Terminated for {uid}.`")

@client.on(events.NewMessage(incoming=True))
async def multi_echo_engine(event):
    if getattr(event, 'sender_id', None) in ECHO_LIST:
        await event.reply(event.text or "", file=event.media)

@client.on(events.NewMessage(pattern=r'\.tagall', outgoing=True))
async def tag_all_members(event):
    if not event.is_group: return
    await event.delete()
    async for user in client.iter_participants(event.chat_id):
        if not user.bot:
            await client.send_message(event.chat_id, f"🔱 [{user.first_name}](tg://user?id={user.id}) `Oye Sun!`")
            await asyncio.sleep(0.3)

@client.on(events.NewMessage(pattern=r'\.stopall', outgoing=True))
async def stop_everything(event):
    global SPAM_RUNNING, ECHO_LIST
    SPAM_RUNNING = False
    ECHO_LIST.clear()
    await safe_edit(event, "🛑 **SUPREME HALT:** `All protocols terminated.`")

# ==========================================================================
# UI & STATUS & ADVANCED HELP MENU
# ==========================================================================

@client.on(events.NewMessage(pattern=r'\.alive', outgoing=True))
async def animated_alive(event):
    frames = [
        "🌑 `[INITIALIZING SYSTEM...]`",
        "🌘 `[BYPASSING FIREWALLS...]`",
        "🌗 `[DECRYPTING VAULT...]`",
        "🌖 `[ESTABLISHING CONNECTION...]`",
        "🌕 **BHAYANKAR V18 SUPREME IS ALIVE** 🔱"
    ]
    for frame in frames:
        await event.edit(frame)
        await asyncio.sleep(0.3)

    uptime = str(datetime.now() - START_TIME).split('.')[0]
    final_msg = f"""
**🔱 BHAYANKAR SUPREME V18 🔱**
➖➖➖➖➖➖➖➖➖➖
⏱ **Uptime:** `{uptime}`
🗄 **Saved Profiles:** `{len(SAVED_PROFILES)}`
📣 **Active Echoes:** `{len(ECHO_LIST)}`
🛡 **Status:** `God Mode Active` 🟢
➖➖➖➖➖➖➖➖➖➖
"""
    await event.edit(final_msg)

@client.on(events.NewMessage(pattern=r'\.help(?:\s+(.*))?', outgoing=True))
async def dynamic_help_menu(event):
    module = event.pattern_match.group(1)
    
    if not module:
        main_menu = """
**💀 ıllıllı 𝕭𝖍𝖆𝖞𝖆𝖓𝖐𝖆𝖗 𝕾𝖚𝖕𝖗𝖊𝖒𝖊 ıllıllı 💀**
➖➖➖➖➖➖➖➖➖➖➖➖
**🔹 MODULES MENU 🔹**
Toh bhai, kis module ke baare mein janna hai? Niche diye command type karo:

➔ `.help id` (Identity & Clone System)
➔ `.help vault` (Profile Save & Load)
➔ `.help attack` (Spam, Echo, Tagall)
➔ `.help extra` (DotArt & View-Once Saver)
➔ `.help system` (Alive, Stopall)
➖➖➖➖➖➖➖➖➖➖➖➖
*Usage: Type `.help attack` to see attack commands.*
"""
        await safe_edit(event, main_menu)

    elif module.lower() == "id":
        msg = "**🎭 ELITE IDENTITY SYSTEM 🎭**\n"
        msg += "`Ye module dusro ki DP/Bio churane aur wapas apne real account par aane ke liye hai.`\n\n"
        msg += "• `.clone` - Kisi ke message par reply karo, bot uska DP aur Bio copy kar lega.\n"
        msg += "• `.revert` - Apna original DP aur Bio wapas laane ke liye."
        await safe_edit(event, msg)

    elif module.lower() == "vault":
        msg = "**💾 PROFILE VAULT SYSTEM 💾**\n"
        msg += "`Ye module profiles ko hamesha ke liye save karne ke kaam aata hai.`\n\n"
        msg += "• `.saveprofile [name]` - Apna ya reply kiye bande ka profile save karo.\n"
        msg += "• `.loadprofile [name]` - Save ki hui profile laga lo.\n"
        msg += "• `.delprofile [name]` - Profile delete karne ke liye.\n"
        msg += "• `.profiles` - Saari saved profiles ki list dekho."
        await safe_edit(event, msg)

    elif module.lower() == "attack":
        msg = "**⚔️ ATTACK PROTOCOLS ⚔️**\n"
        msg += "`Groups aur DM mein tabahi machane ke liye.`\n\n"
        msg += "• `.spam [count] [delay] [msg]` - Ex: `.spam 50 0.5 Hello`\n"
        msg += "• `.echo` - Reply karke use karo. Target jo bolega, bot wahi repeat karega.\n"
        msg += "• `.unecho` - Target ko echo se hatane ke liye.\n"
        msg += "• `.tagall` - Group ke sabhi members ko tag karne ke liye."
        await safe_edit(event, msg)
        
    elif module.lower() == "extra":
        msg = "**🔥 EXTRA SUPREME FEATURES 🔥**\n"
        msg += "`Khatarnak hacks aur Art.`\n\n"
        msg += "• `.vo on` ya `.vo off` - Anti-View-Once system. Agar ON hai toh View-Once media tumhare Saved Messages mein jayega.\n"
        msg += "• `.dotart [text]` - Kisi bhi text/number ko Hacker Style (Emoji Dots) mein convert karega. Ex: `.dotart HACK`"
        await safe_edit(event, msg)
        
    elif module.lower() == "system":
        msg = "**🛑 SYSTEM CONTROLS 🛑**\n\n"
        msg += "• `.stopall` - Chalte hue Spam ya Echo ko turant rokne ke liye (Emergency Killswitch).\n"
        msg += "• `.alive` - Bot ka status, uptime aur info check karne ke liye."
        await safe_edit(event, msg)
    else:
        await safe_edit(event, "❌ **Error:** Aisa koi module nahi hai. Sirf `.help` likho menu dekhne ke liye.")

print("\n[+] BHAYANKAR V18 ELITE IS NOW LIVE!")
client.start()
client.run_until_disconnected()
