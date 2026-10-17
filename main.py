import json
import logging
import os
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, CommandHandler, MessageHandler, filters, ContextTypes

# --- FLASK SERVER (24/7 Active rakhne ke liye) ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is Alive and Running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# --- Tera Bot Token aur Admin ID ---
BOT_TOKEN = "8870037435:AAHFVV4uCBAkroUtaBs7NVzG7KmjJulvo7c"
ADMIN_ID = 8343576029                   
USERS_FILE = "users.json"
VOICE_FILE_ID_FILE = "voice_id.txt"
WELCOME_MSG_FILE = "welcome_msg.json"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def save_user(user_id):
    users = []
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                users = json.load(f)
        except:
            users = []
    if user_id not in users:
        users.append(user_id)
        try:
            with open(USERS_FILE, "w") as f:
                json.dump(users, f)
        except Exception as e:
            print(f"Error saving user: {e}")

def get_all_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def get_saved_voice_id():
    if os.path.exists(VOICE_FILE_ID_FILE):
        with open(VOICE_FILE_ID_FILE, "r") as f:
            return f.read().strip()
    return None

def get_saved_welcome_message():
    if os.path.exists(WELCOME_MSG_FILE):
        try:
            with open(WELCOME_MSG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None
    return None

# --- 1. Join Request aate hi data save karna aur Name ke sath Welcome message bhejna ---
async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request = update.chat_join_request
    user = request.from_user
    user_id = user.id
    user_name = user.first_name  # Bande ka naam yahan uthega
    
    save_user(user_id)

    welcome_data = get_saved_welcome_message()
    if welcome_data:
        try:
            if welcome_data.get("type") == "text":
                # Naam ko message ke aage ya shuruat mein jod rahe hain
                custom_text = f"<b>{user_name}</b>, {welcome_data['text']}"
                await context.bot.send_message(
                    chat_id=user_id, 
                    text=custom_text, 
                    parse_mode="HTML"
                )
            elif welcome_data.get("type") == "photo":
                # Photo wale message mein caption ke aage naam jod rahe hain
                original_caption = welcome_data.get("caption", "")
                custom_caption = f"<b>{user_name}</b>, {original_caption}" if original_caption else f"<b>{user_name}</b>"
                await context.bot.send_photo(
                    chat_id=user_id, 
                    photo=welcome_data["file_id"], 
                    caption=custom_caption,
                    parse_mode="HTML"
                )
        except Exception as e:
            print(f"Error sending custom welcome message: {e}")
    else:
        try:
            await context.bot.send_message(chat_id=user_id, text=f"Hello {user_name}!")
        except Exception as e:
            print(f"Error sending default text: {e}")

    saved_voice = get_saved_voice_id()
    if saved_voice:
        try:
            await context.bot.send_voice(chat_id=user_id, voice=saved_voice)
        except Exception as e:
            print(f"Error sending voice note: {e}")

# --- 2. Text Broadcast Command ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Tu is command ko use nahi kar sakta!")
        return

    message_text = " ".join(context.args)
    if not message_text:
        await update.message.reply_text("❌ Kripya message likhein, jaise: /broadcast aapka sandesh")
        return

    users = get_all_users()
    if users:
        success = 0
        failed = 0
        status_msg = await update.message.reply_text("📤 Broadcast shuru ho gaya hai...")
        
        for user_id in users:
            try:
                await context.bot.send_message(chat_id=user_id, text=message_text)
                success += 1
            except Exception as e:
                failed += 1
        
        await status_msg.edit_text(f"✅ Broadcast pura hua!\n\n Safal: {success}\n Asafal: {failed}")
    else:
        await update.message.reply_text("❌ Koi user database nahi mila!")

# --- 3. Admin Live Chat aur Settings Handler ---
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    if user.id == ADMIN_ID:
        
        # --- Welcome Message Set karne ka tarika (Long press reply karke /setwelcome) ---
        if message.text and message.text.strip() == "/setwelcome":
            if message.reply_to_message:
                source_msg = message.reply_to_message
                welcome_data = {}
                
                if source_msg.text:
                    welcome_data = {
                        "type": "text",
                        "text": source_msg.text
                    }
                elif source_msg.photo:
                    welcome_data = {
                        "type": "photo",
                        "file_id": source_msg.photo[-1].file_id,
                        "caption": source_msg.caption or ""
                    }

                if welcome_data:
                    with open(WELCOME_MSG_FILE, "w", encoding="utf-8") as f:
                        json.dump(welcome_data, f, ensure_ascii=False)
                    await message.reply_text("✨ Premium welcome message safaltapurvak set ho gaya hai!")
                else:
                    await message.reply_text("❌ Jiss message par reply kiya hai usme text ya photo honi chahiye.")
            else:
                await message.reply_text("❌ Kripya apne us message par long press karke reply karein jise welcome banana hai aur likhein: /setwelcome")
            return

        # Voice note parmanent set karne ke liye (/setvoice)
        if message.voice and message.caption and message.caption.strip() == "/setvoice":
            with open(VOICE_FILE_ID_FILE, "w") as f:
                f.write(message.voice.file_id)
            await message.reply_text("✅ Voice note parmanent set ho gaya hai!")
            return

        # Voice note sabko ek saath bhejne ke liye (/broadcast_voice)
        if message.voice and message.caption and message.caption.strip() == "/broadcast_voice":
            voice_file_id = message.voice.file_id
            users = get_all_users()
            
            if users:
                success = 0
                failed = 0
                status_msg = await message.reply_text("🎙️ Voice note broadcast shuru ho raha hai...")
                
                for user_id in users:
                    try:
                        await context.bot.send_voice(chat_id=user_id, voice=voice_file_id)
                        success += 1
                    except Exception as e:
                        failed += 1
                
                await status_msg.edit_text(f"✅ Voice note broadcast pura hua!\n\n Safal: {success}\n Asafal: {failed}")
            else:
                await message.reply_text("❌ Koi user database nahi mila!")
            return

        # Agar admin kisi user ke message par reply kare
        if message.reply_to_message:
            replied_text = message.reply_to_message.text or message.reply_to_message.caption
            if replied_text and "User ID:" in replied_text:
                try:
                    line = [l for l in replied_text.split('\n') if "User ID:" in l][0]
                    target_user_id = int(line.split(":")[1].strip())
                    
                    if message.voice:
                        await context.bot.send_voice(chat_id=target_user_id, voice=message.voice.file_id)
                    elif message.text:
                        await context.bot.send_message(chat_id=target_user_id, text=message.text)
                    
                    await message.reply_text("✅ Message user ko bhej diya gaya hai!")
                except Exception as g:
                    await message.reply_text(f"❌ Bhejne mein error aaya: {g}")
        return

    else:
        save_user(user.id)
        
        user_name = user.full_name
        username = f"@{user.username}" if user.username else "Koi username nahi"
        
        forward_header = f"📩 Naya message aaya hai!\n👤 Naam: {user_name}\n🔗 Username: {username}\n🆔 User ID: {user.id}\n-------------------\n"
        
        try:
            if message.text:
                await context.bot.send_message(chat_id=ADMIN_ID, text=forward_header + message.text)
            elif message.voice:
                await context.bot.send_message(chat_id=ADMIN_ID, text=forward_header + "[Neeche user ka voice note hai]")
                await context.bot.send_voice(chat_id=ADMIN_ID, voice=message.voice.file_id)
            elif message.photo:
                await context.bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=forward_header + (message.caption or ""))
            else:
                await context.bot.send_message(chat_id=ADMIN_ID, text=forward_header + "[User ne media bheja hai]")
        except Exception as e:
                print(f"Error forwarding to admin: {e}")

if __name__ == '__main__':
    keep_alive()
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_messages))

    print("Bot started successfully...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
