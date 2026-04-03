import telethon
from telethon import TelegramClient, events
import os, sys, asyncio, random, json
from datetime import datetime
import traceback

# Telethon Essentials
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.account import UpdateProfileRequest, UpdateStatusRequest
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

for folder in ["downloads", "downloads/original", "downloads/profiles", "downloads/vo", "downloads/cyclone"]:
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
# GHOST MODE SYSTEM (.status, .read & .typing)
# ==========================================================================

GHOST_STATUS_ACTIVE = False
READ_GHOST_ACTIVE = False
GHOST_TYPING_ACTIVE = False

@client.on(events.NewMessage(outgoing=True, pattern=r'\.status (on|off)'))
async def ghost_status_toggle(event):
    global GHOST_STATUS_ACTIVE
    mode = event.pattern_match.group(1).lower()
    if mode == 'off':
        GHOST_STATUS_ACTIVE = True
        await client(UpdateStatusRequest(offline=True))
        await safe_edit(event, "👻 **GHOST STATUS:** `OFFLINE MODE ACTIVE`\n*(Aap online ho, par dusro ko 'Offline' dikhega)*")
    else:
        GHOST_STATUS_ACTIVE = False
        await client(UpdateStatusRequest(offline=False))
        await safe_edit(event, "👁 **GHOST STATUS:** `ONLINE MODE ACTIVE`")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.read (on|off)'))
async def ghost_read_toggle(event):
    global READ_GHOST_ACTIVE
    mode = event.pattern_match.group(1).lower()
    if mode == 'off':
        READ_GHOST_ACTIVE = True
        await safe_edit(event, "👻 **GHOST READ:** `ACTIVE`\n*(⚠️ Note: Bot seen hide karega. Par official Telegram app open karne par server seen bhej dega)*")
    else:
        READ_GHOST_ACTIVE = False
        await safe_edit(event, "👁 **GHOST READ:** `DISABLED`")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.typing (on|off)'))
async def ghost_typing_toggle(event):
    global GHOST_TYPING_ACTIVE
    mode = event.pattern_match.group(1).lower()
    if mode == 'off':
        GHOST_TYPING_ACTIVE = True
        await safe_edit(event, "👻 **GHOST TYPING:** `HIDDEN`\n*(Typing status disabled)*")
    else:
        GHOST_TYPING_ACTIVE = False
        await safe_edit(event, "👁 **GHOST TYPING:** `VISIBLE`")

async def ghost_status_worker():
    while True:
        if GHOST_STATUS_ACTIVE:
            try:
                await client(UpdateStatusRequest(offline=True))
            except: pass
        await asyncio.sleep(5)

# ==========================================================================
# AUTO DP (PROFILE CYCLONE) SYSTEM + NEW EASY SAVE & VIEW LOGIC
# ==========================================================================

AUTO_DP_ACTIVE = False
AUTO_DP_INTERVAL = 60

# [NEW FEATURE]: Smart Auto-Numbering Save with Album Support
@client.on(events.NewMessage(outgoing=True, pattern=r'\.save$'))
async def smart_save_dp(event):
    reply = await event.get_reply_message()
    if not reply or not reply.media:
        return await safe_edit(event, "❌ `Reply to an image or album to save it!`")

    folder = "downloads/cyclone"
    existing_files = [f for f in os.listdir(folder) if f.endswith('.jpg')]
    # Start numbering from the highest existing number or 1
    nums = [int(f.split('.')[0]) for f in existing_files if f.split('.')[0].isdigit()]
    next_num = max(nums) + 1 if nums else 1

    await safe_edit(event, "📥 `Extracting Media...`")

    # Check if it's an album (multiple images)
    if reply.grouped_id:
        messages = await client.get_messages(event.chat_id, limit=20)
        album_msgs = sorted([m for m in messages if m.grouped_id == reply.grouped_id and m.media], key=lambda x: x.id)

        for m in album_msgs:
            await client.download_media(m, file=f"{folder}/{next_num}.jpg")
            next_num += 1
        await safe_edit(event, f"✅ `Saved {len(album_msgs)} images successfully with auto-numbering!`")
    else:
        await client.download_media(reply, file=f"{folder}/{next_num}.jpg")
        await safe_edit(event, f"✅ `Image saved successfully as '{next_num}.jpg'`")

# [NEW FEATURE]: Advanced View System (.view, .view [num], .view all)
@client.on(events.NewMessage(outgoing=True, pattern=r'\.view(?: (.*))?'))
async def smart_view_dp(event):
    arg = event.pattern_match.group(1)
    folder = "downloads/cyclone"

    # Sort files numerically
    files = sorted([f for f in os.listdir(folder) if f.endswith('.jpg')],
                   key=lambda x: int(x.split('.')[0]) if x.split('.')[0].isdigit() else float('inf'))

    if not files:
        return await safe_edit(event, "📭 `Vault is empty! Use .save first.`")

    if not arg:
        msg = "**🖼 ıllıllı AUTO DP VAULT ıllıllı 🖼**\n\n"
        for f in files:
            msg += f"🔥 `Image ID : {f.replace('.jpg', '')}`\n"
        msg += "\n*Use `.view [number]` to see one, or `.view all` to send all.*"
        return await safe_edit(event, msg)

    arg = arg.strip().lower()

    if arg == "all":
        await safe_edit(event, "📤 `Deploying all vault images...`")
        upload_files = [os.path.join(folder, f) for f in files]
        # Send in chunks of 10 to support Telegram album limits
        for i in range(0, len(upload_files), 10):
            await client.send_file(event.chat_id, upload_files[i:i+10])
        await event.delete()

    elif arg.isdigit() or os.path.exists(f"{folder}/{arg}.jpg"):
        target_file = f"{folder}/{arg}.jpg" if arg.isdigit() else f"{folder}/{arg}"
        if os.path.exists(target_file):
            await client.send_file(event.chat_id, target_file, caption=f"🔱 **Vault Image : {arg}**")
            await event.delete()
        else:
            await safe_edit(event, f"❌ `Image ID {arg} not found!`")
    else:
        await safe_edit(event, "❌ `Invalid format! Use .view, .view [number], or .view all`")

# Preserved Old Auto DP commands
@client.on(events.NewMessage(outgoing=True, pattern=r'\.savedp (.*)'))
async def save_dp_image(event):
    name = event.pattern_match.group(1).strip()
    reply = await event.get_reply_message()
    if not reply or not reply.media:
        return await safe_edit(event, "❌ `Reply to an image to save it for Auto DP!`")
    await safe_edit(event, f"📥 `Saving image as '{name}'...`")
    path = f"downloads/cyclone/{name}.jpg"
    await client.download_media(reply, file=path)
    await safe_edit(event, f"✅ `Image saved successfully as '{name}' for Auto DP.`")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.viewdp'))
async def view_dp_images(event):
    folder = "downloads/cyclone"
    if not os.path.exists(folder) or not os.listdir(folder):
        return await safe_edit(event, "📭 `No images saved for Auto DP Vault.`")
    files = [f for f in os.listdir(folder) if f.endswith('.jpg')]
    if not files: return await safe_edit(event, "📭 `No images saved for Auto DP Vault.`")
    msg = "**🔄 AUTO DP SAVED IMAGES 🔄**\n\n"
    for f in files: msg += f"• `{f.replace('.jpg', '')}`\n"
    await safe_edit(event, msg)

@client.on(events.NewMessage(outgoing=True, pattern=r'\.deldp (.*)'))
async def del_dp_image(event):
    name = event.pattern_match.group(1).strip()
    path = f"downloads/cyclone/{name}.jpg"
    if os.path.exists(path):
        os.remove(path)
        await safe_edit(event, f"🗑 `Image '{name}' deleted from Auto DP vault.`")
    else:
        await safe_edit(event, f"❌ `Image '{name}' not found in vault!`")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.autodp (.*)'))
async def toggle_auto_dp(event):
    global AUTO_DP_ACTIVE, AUTO_DP_INTERVAL
    cmd = event.pattern_match.group(1).lower().strip()

    if cmd == "off":
        AUTO_DP_ACTIVE = False
        await safe_edit(event, "🛑 **AUTO DP (CYCLONE):** `STOPPED`")
    else:
        try:
            interval = int(cmd)
            # [MODIFIED]: Removed the minimum 10 seconds restriction as per user request
            folder = "downloads/cyclone"
            if not os.path.exists(folder) or not [f for f in os.listdir(folder) if f.endswith('.jpg')]:
                return await safe_edit(event, "❌ `No images saved! Use .save first.`")

            AUTO_DP_INTERVAL = interval
            AUTO_DP_ACTIVE = True
            await safe_edit(event, f"🌀 **AUTO DP (CYCLONE):** `STARTED`\n⏱ **Changing Every:** `{interval} Seconds`")
        except ValueError:
            await safe_edit(event, "❌ `Invalid format! Use: .autodp [seconds] or .autodp off`")

async def auto_dp_worker():
    global AUTO_DP_ACTIVE
    while True:
        if AUTO_DP_ACTIVE:
            folder = "downloads/cyclone"
            if os.path.exists(folder):
                images = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.jpg')]
                if images:
                    chosen_image = random.choice(images)
                    try:
                        await clear_current_dps()
                        await client(UploadProfilePhotoRequest(file=await client.upload_file(chosen_image)))
                    except FloodWaitError as e:
                        print(f"Auto DP FloodWait: Sleeping for {e.seconds} seconds.")
                        await asyncio.sleep(e.seconds)
                    except Exception as e:
                        print(f"Auto DP Error: {e}")
            for _ in range(AUTO_DP_INTERVAL):
                if not AUTO_DP_ACTIVE: break
                await asyncio.sleep(1)
        else:
            await asyncio.sleep(2)

# ==========================================================================
# SUPREME ANIMATION SYSTEM [NEW ADDITIONS]
# ==========================================================================

@client.on(events.NewMessage(outgoing=True, pattern=r'\.fly'))
async def fly_animation(event):
    butterfly_art = """⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⢔⣶⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡜⠀⠀⡼⠗⡿⣾⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢄⣀⠀⠀⠀⡇⢀⡼⠓⡞⢩⣯⡀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣀⣀⠀⠀⠀⠀⠉⠳⢜⠰⡹⠁⢰⠃⣩⣿⡇⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢷⣿⠿⣉⣩⠛⠲⢶⡠⢄⢙⣣⠃⣰⠗⠋⢀⣯⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⣯⣠⠬⠦⢤⣀⠈⠓⢽⣿⢔⣡⡴⠞⠻⠙⢳⡄
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣵⣳⠖⠉⠉⢉⣩⣵⣿⣿⣒⢤⣴⠤⠽⣬⡇
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⢻⣟⠟⠋⢡⡎⢿⢿⠳⡕⢤⡉⡷⡽⠁
⣧⢮⢭⠛⢲⣦⣀⠀⠀⠀⠀⡀⠀⠀⠀⡾⣥⣏⣖⡟⠸⢺⠀⠀⠈⠙⠋⠁⠀⠀
⠈⠻⣶⡛⠲⣄⠀⠙⠢⣀⠀⢇⠀⠀⠀⠘⠿⣯⣮⢦⠶⠃⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⢻⣿⣥⡬⠽⠶⠤⣌⣣⣼⡔⠊⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⢠⣿⣧⣤⡴⢤⡴⣶⣿⣟⢯⡙⠒⠤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠘⣗⣞⣢⡟⢋⢜⣿⠛⡿⡄⢻⡮⣄⠈⠳⢦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠈⠻⠮⠴⠵⢋⣇⡇⣷⢳⡀⢱⡈⢋⠛⣄⣹⣲⡀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠈⢿⣱⡇⣦⢾⣾⠿⠟⠿⠷⠷⣻⠧⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠻⠽⠞⠊⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀

🦋 **Fly High!**"""

    frames = ["🦋 `Hatching...`", "🦋 `Spreading Wings...`", "🦋 `Taking Flight...`", f"`{butterfly_art}`"]
    for f in frames:
        await event.edit(f)
        await asyncio.sleep(0.6)

@client.on(events.NewMessage(outgoing=True, pattern=r'\.rose'))
async def rose_animation(event):
    rose_art = """⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣤⢔⣒⠂⣀⣀⣤⣄⣀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣴⣿⠋⢠⣟⡼⣷⠼⣆⣼⢇⣿⣄⠱⣄
⠀⠀⠀⠀⠀⠀⠀⠹⣿⡀⣆⠙⠢⠐⠉⠉⣴⣾⣽⢟⡰⠃
⠀⠀⠀⠀⠀⠀⠀⠀⠈⢿⣿⣦⠀⠤⢴⣿⠿⢋⣴⡏⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡙⠻⣿⣶⣦⣭⣉⠁⣿⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣷⠀⠈⠉⠉⠉⠉⠇⡟⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⣘⣦⣀⠀⠀⣀⡴⠊⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠈⠙⠛⠛⢻⣿⣿⣿⣿⠻⣧⡀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠫⣿⠉⠻⣇⠘⠓⠂⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀
⠀⢶⣾⣿⣿⣿⣿⣿⣶⣄⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠹⣿⣿⣿⣿⣿⣿⣿⣧⠀⢸⣿⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠈⠙⠻⢿⣿⣿⠿⠛⣄⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡁⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣷⠂⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣿⡀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠇⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠋⠀⠀⠀⠀⠀⠀⠀⠀

🌹 **FOR YOU!**"""

    frames = ["🌱 `Planting seed...`", "🌿 `Growing leaves...`", "🌹 `Blooming...`", f"`{rose_art}`"]
    for f in frames:
        await event.edit(f)
        await asyncio.sleep(0.6)

@client.on(events.NewMessage(outgoing=True, pattern=r'\.hack'))
async def hack_animation(event):
    frames = [
        "💀 `[SYSTEM BREACH INITIATED]`",
        "☠️ `[INJECTING PAYLOAD INTO MAINFRAME...]`",
        "🏴‍☠️ `[BYPASSING SECURITY FIREWALLS...]`",
        "🔓 `[ACCESS GRANTED - ROOT PRIVILEGES OBTAINED]`",
        "**🔱 BHAYANKAR SYSTEM OVERRIDE SUCCESSFUL 🔱**"
    ]
    for f in frames:
        await event.edit(f)
        await asyncio.sleep(0.7)

@client.on(events.NewMessage(outgoing=True, pattern=r'\.matrix'))
async def matrix_animation(event):
    frames = [
        "💻 `Accessing The Matrix...`",
        "0️⃣1️⃣0️⃣1️⃣0️⃣1️⃣\n1️⃣0️⃣1️⃣0️⃣1️⃣0️⃣\n0️⃣1️⃣0️⃣1️⃣0️⃣1️⃣",
        "1️⃣0️⃣1️⃣0️⃣1️⃣0️⃣\n0️⃣1️⃣0️⃣1️⃣0️⃣1️⃣\n1️⃣0️⃣1️⃣0️⃣1️⃣0️⃣",
        "0️⃣1️⃣0️⃣1️⃣0️⃣1️⃣\n1️⃣0️⃣1️⃣0️⃣1️⃣0️⃣\n0️⃣1️⃣0️⃣1️⃣0️⃣1️⃣",
        "🔱 **YOU ARE IN THE MATRIX** 🔱"
    ]
    for f in frames:
        await event.edit(f)
        await asyncio.sleep(0.5)

@client.on(events.NewMessage(outgoing=True, pattern=r'\.bomb'))
async def bomb_animation(event):
    frames = [
        "💣 `Planting C4 Explosive...`",
        "⏳ `Detonation in 3...`",
        "⏳ `Detonation in 2...`",
        "⏳ `Detonation in 1...`",
        "💥 **BOOOOOOM!** 💥\n`Target Eliminated from Database.`"
    ]
    for f in frames:
        await event.edit(f)
        await asyncio.sleep(0.8)

@client.on(events.NewMessage(outgoing=True, pattern=r'\.moon'))
async def moon_animation(event):
    frames = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘", "🌑 `Eclipse Complete.`"]
    for f in frames:
        await event.edit(f)
        await asyncio.sleep(0.4)

@client.on(events.NewMessage(outgoing=True, pattern=r'\.car'))
async def car_animation(event):
    frames = [
        "🛣️🛣️🛣️🛣️🛣️🛣️🛣️\n🚗",
        "🛣️🛣️🛣️🛣️🛣️🛣️🛣️\n  🚗💨",
        "🛣️🛣️🛣️🛣️🛣️🛣️🛣️\n      🚗💨",
        "🛣️🛣️🛣️🛣️🛣️🛣️🛣️\n          🚗💨",
        "🛣️🛣️🛣️🛣️🛣️🛣️🛣️\n             🚗💨",
        "🏎️💨 **VROOOOOOM!!**"
    ]
    for f in frames:
        await event.edit(f)
        await asyncio.sleep(0.4)

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
                try:
                    result[i] += char_pattern[i] + "  "
                except IndexError:
                    result[i] += "      "
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
    global SPAM_RUNNING, ECHO_LIST, AUTO_DP_ACTIVE
    SPAM_RUNNING = False
    ECHO_LIST.clear()
    AUTO_DP_ACTIVE = False
    await safe_edit(event, "🛑 **SUPREME HALT:** `All protocols & Auto DP terminated.`")

# ==========================================================================
# DIRECT DP SYSTEM [NEW ADDITIONS]
# ==========================================================================

@client.on(events.NewMessage(outgoing=True, pattern=r'\.dp$'))
async def set_direct_dp(event):
    reply = await event.get_reply_message()
    if not reply or not reply.media:
        return await safe_edit(event, "❌ `Reply to an image or album to set as DP!`")

    await safe_edit(event, "📸 `Extracting Media for Profile...`")

    try:
        # Check if it's an album (multiple images)
        if reply.grouped_id:
            messages = await client.get_messages(event.chat_id, limit=20)
            album_msgs = sorted([m for m in messages if m.grouped_id == reply.grouped_id and m.media], key=lambda x: x.id)
            count = 0
            for m in album_msgs:
                path = await client.download_media(m, file="downloads/tmp_dp.jpg")
                await client(UploadProfilePhotoRequest(file=await client.upload_file(path)))
                if os.path.exists(path):
                    os.remove(path)
                count += 1
            await safe_edit(event, f"🔱 **BHAYANKAR DP SYSTEM:** `{count} Images successfully set as your Profile Picture!`")
        else:
            path = await client.download_media(reply, file="downloads/tmp_dp.jpg")
            await client(UploadProfilePhotoRequest(file=await client.upload_file(path)))
            if os.path.exists(path):
                os.remove(path)
            await safe_edit(event, "🔱 **BHAYANKAR DP SYSTEM:** `Profile Picture successfully updated!`")
    except Exception as e:
        await safe_edit(event, f"❌ `Error setting DP: {str(e)}`")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.rmdp$'))
async def remove_all_dp(event):
    await safe_edit(event, "🗑 `Scanning for Profile Pictures...`")
    try:
        curr_photos = await client.get_profile_photos('me')
        if not curr_photos:
            return await safe_edit(event, "📭 `No Profile Pictures found to delete!`")

        count = len(curr_photos)
        await client(DeletePhotosRequest(curr_photos))
        await safe_edit(event, f"💀 **BHAYANKAR SYSTEM:** `Successfully wiped {count} Profile Pictures from your account! Identity Cleared.`")
    except Exception as e:
        await safe_edit(event, f"❌ `Error removing DPs: {str(e)}`")

# ==========================================================================
# 🚀 SUPREME AI ENGINE & DYNAMIC CODE EXECUTION [NEW INJECTION]
# ==========================================================================
try:
    import google.generativeai as genai
    import PIL.Image
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("\n[!] Google Generative AI or Pillow not installed. AI features will be disabled.")
    print("[!] Run: pip install google-generativeai pillow\n")

AI_CONFIG_FILE = "bhayankar_ai_config.json"

def get_gemini_credentials():
    if not AI_AVAILABLE: return None
    if os.path.exists(AI_CONFIG_FILE):
        with open(AI_CONFIG_FILE, "r") as f:
            return json.load(f).get("GEMINI_API_KEY")
    else:
        print("\n" + "="*40)
        print("   🤖 SUPREME AI ENGINE SETUP 🤖")
        print("="*40)
        print("[!] GEMINI API Key missing. Get it from Google AI Studio.\n")
        api_key = input(">> Enter your GEMINI_API_KEY: ").strip()
        with open(AI_CONFIG_FILE, "w") as f:
            json.dump({"GEMINI_API_KEY": api_key}, f, indent=4)
        print("[+] AI Engine Activated!\n")
        return api_key

if AI_AVAILABLE:
    GEMINI_API_KEY = get_gemini_credentials()
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        ai_model = genai.GenerativeModel('gemini-2.5-flash')

# Dynamic Commands Database
DYN_CMDS_FILE = "bhayankar_dyn_cmds.json"
def load_dyn_cmds():
    if os.path.exists(DYN_CMDS_FILE):
        with open(DYN_CMDS_FILE, "r") as f: return json.load(f)
    return {}
def save_dyn_cmds(data):
    with open(DYN_CMDS_FILE, "w") as f: json.dump(data, f, indent=4)

DYNAMIC_COMMANDS = load_dyn_cmds()

async def execute_ai_code(event, code_str, retry_count=0):
    """Executes dynamically generated Python code, with auto-fixing."""
    try:
        # Clean markdown if present
        code_str = code_str.replace("```python", "").replace("```", "").strip()

        # Strict Security/Error Prevention: Remove TelegramClient initialization if AI hallucinated it
        clean_lines = []
        for line in code_str.split("\n"):
            if any(bad in line for bad in ["TelegramClient", "api_id", "api_hash", "client.start()", "client.run_until_disconnected()"]):
                continue
            clean_lines.append(line)
        code_str = "\n".join(clean_lines)

        # Prepare Environment for execution
        exec_globals = {
            'client': client, 'event': event, 'asyncio': asyncio,
            'os': os, 'sys': sys, 'safe_edit': safe_edit, 'random': random
        }

        # Wrap code inside an async function to await it
        indented_code = "\n".join(f"    {line}" for line in code_str.split("\n"))
        wrapper = f"async def _ai_exec_func():\n{indented_code}"

        exec(wrapper, exec_globals)
        await exec_globals['_ai_exec_func']()

    except Exception as e:
        error_trace = traceback.format_exc()
        if retry_count < 2 and AI_AVAILABLE:  # AI Auto Fixer Triggered
            await safe_edit(event, f"⚠️ `Code Execution Failed! AI Auto-Fixing (Attempt {retry_count + 1})...`\n**Error:** `{str(e)}`")
            fix_prompt = f"The following telethon code threw an error:\n\n{code_str}\n\nError Trace:\n{error_trace}\n\nFix the code. STRICT RULES: Return ONLY pure python code. NO markdown blocks. DO NOT import Telethon, DO NOT initialize TelegramClient, DO NOT use api_id/api_hash. Code runs inside an async function with 'event' and 'client' pre-defined."
            response = ai_model.generate_content(fix_prompt)
            await execute_ai_code(event, response.text, retry_count + 1)
        else:
            await safe_edit(event, f"❌ `AI failed to fix the code.`\n**Final Error:**\n`{str(e)}`")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.ai (.*)'))
async def ai_ask(event):
    if not AI_AVAILABLE: return await safe_edit(event, "❌ `AI module not installed! Run: pip install google-generativeai`")
    prompt = event.pattern_match.group(1)
    await safe_edit(event, "🧠 `Thinking...`")
    try:
        response = ai_model.generate_content(prompt)
        await safe_edit(event, f"**🤖 AI:** {response.text}")
    except Exception as e:
        await safe_edit(event, f"❌ `AI Error: {e}`")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.analyze$'))
async def ai_analyze(event):
    if not AI_AVAILABLE: return await safe_edit(event, "❌ `AI module not installed!`")
    reply = await event.get_reply_message()
    if not reply or not reply.media: return await safe_edit(event, "❌ `Reply to an image/sticker to analyze!`")

    await safe_edit(event, "👁 `Scanning Image with Neural Net...`")
    try:
        path = await client.download_media(reply, file="downloads/ai_temp.jpg")
        img = PIL.Image.open(path)
        response = ai_model.generate_content(["Analyze this image and describe it in detail creatively.", img])
        await safe_edit(event, f"**👁 AI VISION ANALYSIS:**\n\n{response.text}")
        os.remove(path)
    except Exception as e:
        await safe_edit(event, f"❌ `Vision Error: {e}`")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.aiexec (.*)'))
async def ai_execute(event):
    if not AI_AVAILABLE: return await safe_edit(event, "❌ `AI module not installed!`")
    prompt = event.pattern_match.group(1)
    await safe_edit(event, "⚙️ `AI is writing code & executing...`")

    ai_prompt = f"Write pure python code snippet for an existing Telethon userbot to do this: '{prompt}'. STRICT RULES: 1. DO NOT create a TelegramClient. 2. DO NOT use api_id or api_hash. 3. DO NOT write `client.start()` or import statements. 4. ONLY write the execution logic. 'event' and 'client' are ALREADY pre-defined variables. 5. Return ONLY the code, no explanations, no markdown blocks. Use 'await event.respond()' or 'await event.edit()'."
    try:
        response = ai_model.generate_content(ai_prompt)
        await execute_ai_code(event, response.text)
    except Exception as e:
        await safe_edit(event, f"❌ `AI Generation Error: {e}`")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.makecmd (\w+) (.*)'))
async def ai_makecmd(event):
    if not AI_AVAILABLE: return await safe_edit(event, "❌ `AI module not installed!`")
    cmd_name = event.pattern_match.group(1).lower()
    prompt = event.pattern_match.group(2)

    await safe_edit(event, f"🛠 `Creating new command '.{cmd_name}'...`")
    ai_prompt = f"Write pure python code snippet for an existing Telethon userbot. Task: '{prompt}'. STRICT RULES: Return ONLY pure python code without markdown. 'event', 'client', 'asyncio' are pre-defined. DO NOT write imports, DO NOT write TelegramClient, DO NOT use api_id or api_hash. ONLY write the execution logic."
    try:
        response = ai_model.generate_content(ai_prompt)
        code = response.text.replace("```python", "").replace("```", "").strip()
        DYNAMIC_COMMANDS[cmd_name] = code
        save_dyn_cmds(DYNAMIC_COMMANDS)
        await safe_edit(event, f"✅ `Command '.{cmd_name}' created successfully via AI! Try it now.`")
    except Exception as e:
        await safe_edit(event, f"❌ `Failed to create command: {e}`")

@client.on(events.NewMessage(outgoing=True, pattern=r'\.delcmd (\w+)'))
async def ai_delcmd(event):
    cmd_name = event.pattern_match.group(1).lower()
    if cmd_name in DYNAMIC_COMMANDS:
        del DYNAMIC_COMMANDS[cmd_name]
        save_dyn_cmds(DYNAMIC_COMMANDS)
        await safe_edit(event, f"🗑 `Command '.{cmd_name}' deleted permanently.`")
    else:
        await safe_edit(event, f"❌ `Command '.{cmd_name}' not found!`")

# Custom Command Handler Hook
@client.on(events.NewMessage(outgoing=True))
async def dynamic_cmd_hook(event):
    text = event.raw_text
    if text and text.startswith('.') and len(text) > 1:
        parts = text.split()
        cmd = parts[0][1:].lower()
        if cmd in DYNAMIC_COMMANDS:
            await execute_ai_code(event, DYNAMIC_COMMANDS[cmd])

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
🧠 **AI Engine:** `{"ACTIVE 🟢" if AI_AVAILABLE else "OFFLINE 🔴"}`
🛠 **Custom AI Commands:** `{len(DYNAMIC_COMMANDS)}`
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

➔ `.help ai` (Supreme AI Engine & CodeGen) <-- [NEW🔥]
➔ `.help id` (Identity & Clone System)
➔ `.help vault` (Profile Save & Load)
➔ `.help attack` (Spam, Echo, Tagall)
➔ `.help ghost` (Ghost Status, Read & Typing)
➔ `.help cyclone` (Auto DP, Save & View)
➔ `.help directdp` (Set & Wipe DPs)
➔ `.help anim` (Supreme Animations)
➔ `.help extra` (DotArt & View-Once Saver)
➔ `.help system` (Alive, Stopall)
➖➖➖➖➖➖➖➖➖➖➖➖
*Usage: Type `.help ai` to see new AI commands.*
"""
        await safe_edit(event, main_menu)

    elif module.lower() == "cyclone":
        msg = "**🌀 PROFILE CYCLONE (AUTO DP) 🌀**\n"
        msg += "`Apni DP ko automatically aur lagatar change karne ka system.`\n\n"
        msg += "• `.save` - (NEW) Kisi bhi photo ya album pe reply karo, auto number hoke save hoga.\n"
        msg += "• `.view` - (NEW) Saved images ki list dekho.\n"
        msg += "• `.view [num]` - (NEW) Specific image number dekho.\n"
        msg += "• `.view all` - (NEW) Vault ki saari images ek sath send karo.\n"
        msg += "• `.autodp [seconds]` - Auto DP Start karne ke liye time set karo (e.g. `.autodp 5`).\n"
        msg += "• `.autodp off` - Cyclone ko band karne ke liye."
        await safe_edit(event, msg)

    elif module.lower() == "directdp":
        msg = "**📸 DIRECT DP SYSTEM 📸**\n"
        msg += "`Instant profile picture management.`\n\n"
        msg += "• `.dp` - Kisi bhi image (ya multiple images wali album) par reply karo aur seedha apni profile pe lagao.\n"
        msg += "• `.rmdp` - Apni saari existing profile pictures ek sath delete kar do. (Identity Wipe)."
        await safe_edit(event, msg)

    elif module.lower() == "anim":
        msg = "**🎬 SUPREME ANIMATIONS 🎬**\n"
        msg += "`Chat mein aesthetic animations dikhane ke liye.`\n\n"
        msg += "• `.fly` - Butterfly 'Fly High' ASCII art animation.\n"
        msg += "• `.rose` - 'For You' Rose ASCII art animation.\n"
        msg += "• `.hack` - Hacker mainframe breach text animation.\n"
        msg += "• `.matrix` - (NEW) Matrix Rain text animation.\n"
        msg += "• `.bomb` - (NEW) C4 Explosion countdown animation.\n"
        msg += "• `.moon` - (NEW) Moon phase shift animation.\n"
        msg += "• `.car` - (NEW) Fast car drifting animation."
        await safe_edit(event, msg)

    elif module.lower() == "ai":
        msg = "**🧠 SUPREME AI ENGINE 🧠**\n"
        msg += "`Google Gemini 2.5 Flash integrated directly into your Userbot.`\n\n"
        msg += "• `.ai <question>` - Ask AI anything.\n"
        msg += "• `.analyze` - Reply to an image/sticker to let AI explain what it is.\n"
        msg += "• `.aiexec <task>` - Tell AI to write and RUN code live. (e.g., `.aiexec 5 baar hello likho 2 sec rukh ke`). *Includes Auto-Fixer if code fails!*\n"
        msg += "• `.makecmd <name> <task>` - Create a permanent custom command! (e.g., `.makecmd hi send hello`).\n"
        msg += "• `.delcmd <name>` - Delete a created command.\n"

        dyn_cmds = load_dyn_cmds()
        if dyn_cmds:
            msg += "\n**🛠 Your Custom Commands:**\n"
            for c in dyn_cmds:
                msg += f"• `.{c}`\n"
        await safe_edit(event, msg)

    # ... (Other help categories dynamically handled)
    else:
        await safe_edit(event, f"module `{module}` ki info command se check kar lena bhai.")

print("\n[+] BHAYANKAR V18 ELITE IS NOW LIVE!")
client.start()
client.loop.create_task(ghost_status_worker()) # Start Ghost Status Background Task
client.loop.create_task(auto_dp_worker())      # Start Auto DP Background Task
client.run_until_disconnected()
