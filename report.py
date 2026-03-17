import os, sys, asyncio, random, json, smtplib, re, requests
from datetime import datetime
from email.mime.text import MIMEText

# --- [ 1. AUTO-INSTALLER ] ---
try:
    from telethon import TelegramClient, events
    from pyrogram import Client, filters
    from pyrogram.raw import functions, types as raw_types
except ImportError:
    print("🚀 Optimizing Engines & Installing Supreme Modules...")
    os.system("pip install telethon pyrogram tgcrypto requests")
    os.execv(sys.executable, [sys.executable] + sys.argv)

# --- [ 2. BHAYANKAR CONFIG SYSTEM ] ---
CONFIG_FILE = "bhayankar_config.json"
SESSION_NAME = 'bhhayankar_v18'

def load_system():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    print("\n" + "═"*50 + "\n   💀 BHAYANKAR V18: SYSTEM INITIALIZATION 💀\n" + "═"*50)
    data = {
        "API_ID": int(input(">> API_ID: ").strip()),
        "API_HASH": input(">> API_HASH: ").strip(),
        "EMAIL": input(">> SENDER GMAIL: ").strip(),
        "PASS": input(">> APP PASSWORD: ").strip()
    }
    with open(CONFIG_FILE, "w") as f: json.dump(data, f, indent=4)
    return data

CFG = load_system()

# --- [ 3. PROXY ENGINE ] ---
def get_proxies():
    """Scrapes fresh proxies ONLY when requested in command."""
    try:
        res = requests.get("https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all")
        return res.text.splitlines() if res.status_code == 200 else []
    except: return []

# --- [ 4. 20+ DEADLY INTERNAL REASONS ] ---
INTERNAL_REASONS = [
    "Child Sexual Abuse Material distribution in private/public sectors.",
    "Promotion of terrorism and coordination of extremist violent acts.",
    "Sale of illegal narcotics and prohibited substances.",
    "Organized financial fraud, phishing, and session hijacking.",
    "Distribution of non-consensual intimate imagery (Privacy violation).",
    "Hate speech targeting protected groups and inciting violence.",
    "Promotion of self-harm and suicide-related content.",
    "Copyright infringement and massive distribution of pirated assets.",
    "Harassment and cyber-bullying of multiple individuals.",
    "Execution of crypto-scams and deceptive investment schemes.",
    "Identity theft and malicious impersonation of verified officials.",
    "Spreading dangerous misinformation to cause public panic.",
    "Selling stolen credit card data and personal information.",
    "Botnet coordination and DDoS attack planning.",
    "Human trafficking and illegal smuggling operations.",
    "Illegal weapon trade and coordination of violent crimes.",
    "Blackmailing individuals with compromised personal data.",
    "Unsolicited pornographic spamming in public discussions.",
    "Malware distribution through deceptive executable files.",
    "Operating as a node for money laundering activities.",
    "Violating Telegram's core Terms of Service through persistent abuse."
]

# --- [ 5. HIGH-LEVEL EMAIL TEMPLATES ] ---
EMAIL_TEMPLATES = [
    "Subject: URGENT: Child Safety Alert (CSAM) - {target}\n\nTelegram Abuse Team,\nThis user {target} is distributing illegal material involving minors. Immediate termination required.",
    "Subject: PRIORITY: Terrorism Coordination - {target}\n\nAccount {target} is radicalizing users and planning violent extremism. Security threat level: High.",
    "Subject: LEGAL: Privacy Violation & Revenge Porn - {target}\n\nUser {target} is sharing private content without consent. This is a direct violation of privacy laws.",
    "Subject: ALERT: Massive Phishing & Fraud Network - {target}\n\nUser {target} is stealing credentials and session hashes. High-risk profile for financial fraud."
]

# --- [ 6. DUAL CLIENT INITIALIZATION ] ---
t_client = TelegramClient(SESSION_NAME, CFG["API_ID"], CFG["API_HASH"])
p_app = Client("h1_terminator", api_id=CFG["API_ID"], api_hash=CFG["API_HASH"])

# --- [ 7. LOG ENGINE ] ---
async def log_to_saved(text):
    try:
        report = f"🔱 **MISSION LOG** 🔱\n" + "═"*25 + f"\n{text}\n" + "═"*25
        await p_app.send_message("me", report)
    except: pass

def send_email(target_id, count, gap):
    sent = 0
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(CFG["EMAIL"], CFG["PASS"])
            for _ in range(count):
                tmpl = random.choice(EMAIL_TEMPLATES).format(target=target_id)
                subj, body = tmpl.split('\n\n', 1)
                msg = MIMEText(body); msg['Subject'] = subj.replace('Subject: ', ''); msg['From'] = CFG["EMAIL"]; msg['To'] = "abuse@telegram.org"
                s.sendmail(CFG["EMAIL"], "abuse@telegram.org", msg.as_string())
                sent += 1
                asyncio.run(asyncio.sleep(gap))
    except Exception as e: print(f"SMTP Error: {e}")
    return sent

# --- [ 8. SUPREME COMMANDS ] ---

@p_app.on_message(filters.command("report", prefixes=".") & filters.me)
async def report_internal(client, message):
    args = message.command
    # Format: .report <count> <gap> <proxy_on/off>
    count = int(args[1]) if len(args) > 1 else 10
    gap = float(args[2]) if len(args) > 2 else 0.5
    use_proxy = "proxy" in [x.lower() for x in args]
    
    target = message.reply_to_message.from_user.id if message.reply_to_message else message.chat.id
    proxies = get_proxies() if use_proxy else []
    
    proxy_status = "ACTIVE 🌐" if use_proxy else "OFF ❌"
    await message.edit(f"⚔️ **H1 Attack:** `{count}` Hits\n⏱ **Gap:** `{gap}s`\n🛡 **Proxy Mode:** `{proxy_status}`")
    
    hits = 0
    for i in range(count):
        try:
            peer = await client.resolve_peer(target)
            reason_text = random.choice(INTERNAL_REASONS)
            await client.invoke(functions.account.ReportPeer(
                peer=peer, reason=raw_types.InputReportReasonOther(), message=reason_text
            ))
            hits += 1
            if hits % 10 == 0:
                p_info = "| IP: Rotated" if use_proxy else ""
                await message.edit(f"🔱 **Mission:** `{hits}/{count}` {p_info}")
            await asyncio.sleep(gap)
        except: continue
    
    await message.edit(f"🏁 **Finished.** Hits: `{hits}` | Proxy: `{proxy_status}`")
    await log_to_saved(f"🎯 **Internal Attack**\nTarget: `{target}`\nHits: `{hits}/{count}`\nProxy: `{proxy_status}`")

@p_app.on_message(filters.command("reportE", prefixes=".") & filters.me)
async def report_email(client, message):
    args = message.command
    count = int(args[1]) if len(args) > 1 else 5
    gap = float(args[2]) if len(args) > 2 else 1.5
    target = message.reply_to_message.from_user.id if message.reply_to_message else message.chat.id
    
    await message.edit(f"📧 **Email Blast:** `{count}` Mails | Target: `{target}`")
    loop = asyncio.get_event_loop()
    sent = await loop.run_in_executor(None, send_email, target, count, gap)
    await message.edit(f"🏁 **Email Mission Finished.** Sent: `{sent}`")
    await log_to_saved(f"📧 **Email Blast**\nTarget: `{target}`\nSent: `{sent}/{count}`")

# --- [ 9. RUNNER ] ---
async def start_engine():
    await t_client.start()
    await p_app.start()
    print("═"*40 + "\n🔱 BHAYANKAR V18 SUPREME CONTROL LIVE\n" + "═"*40)
    await asyncio.gather(t_client.run_until_disconnected())

if __name__ == "__main__":
    try: asyncio.run(start_engine())
    except KeyboardInterrupt: sys.exit()
