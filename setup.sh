#!/data/data/com.termux/files/usr/bin/bash

# Clear screen for professional look
clear

echo -e "\033[1;31m"
echo "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═"
echo "   💀 BHAYANKAR V18: ENVIRONMENT INSTALLER 💀"
echo "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═"
echo -e "\033[0m"

echo -e "\033[1;34m[*] Step 1: Updating System Packages...\033[0m"
pkg update -y && pkg upgrade -y

echo -e "\033[1;34m[*] Step 2: Installing Python & Essential Tools...\033[0m"
pkg install python git clang make libffi openssl termux-api -y

echo -e "\033[1;34m[*] Step 3: Upgrading Pip...\033[0m"
pip install --upgrade pip

echo -e "\033[1;34m[*] Step 4: Installing All Required Python Libraries...\033[0m"
# Saari libraries jo tumhare userbot aur reporter ke liye chahiye
pip install telethon pyrogram tgcrypto requests aiohttp pyaes hachoir

echo -e "\033[1;32m"
echo "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═"
echo "   ✅ SETUP COMPLETE: SYSTEM IS READY! ✅"
echo "   Now you can run: python bhayankar.py"
echo "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═" "═"
echo -e "\033[0m"
