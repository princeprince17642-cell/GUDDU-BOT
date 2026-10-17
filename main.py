import json
import logging
import os
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, CommandHandler, MessageHandler, filters, ContextTypes

# --- FLASK SERVER (24/7 Active रखने के लिए) ---
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

# --- तेरा Bot Token और Admin ID ---
BOT_TOKEN = "8870037435:AAHFVV4uCBAkroUtaBs7NVzG7KmjJulvo7c"
ADMIN_ID = 8343576029                   
USERS_FILE = "users.json"
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

def get_saved_welcome_messages():
    if os.path.exists(WELCOME_MSG_FILE):
        try:
            with open(WELCOME_MSG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return [data]
        except:
            return []
    return []

# --- 1. Join Request आते ही सीक्वेंस से सारे वेलकम मैसेज भेजना ---
async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request = update.chat_join_request
    user = request.from_user
    user_id = user.id
    user_name = user.first_name or "User"
    
    save_user(user_id)

    welcome_list = get_saved_welcome_messages()
    if welcome_list:
        for index, welcome_data in enumerate(welcome_list):
            try:
                msg_type = welcome_data.get("type")
                is_first = (index == 0)
                
                if msg_type == "text":
                    text_content = welcome_data.get('text', '')
                    entities = welcome_data.get("entities", [])
                    
                    if is_first:
                        prefix = f"{user_name}, "
                        prefix_len = len(prefix.encode('utf-16-le')) // 2
                        
                        adjusted_entities = []
                        for e in entities:
                            e_copy = e.copy()
                            e_copy['offset'] += prefix_len
                            adjusted_entities.append(e_copy)
                        
                        final_text = prefix + text_content
                        await context.bot.send_message(
                            chat_id=user_id, 
                            text=final_text, 
                            entities=adjusted_entities
                        )
                    else:
                        await context.bot.send_message(
                            chat_id=user_id, 
                            text=text_content, 
                            entities=entities
                        )

                elif msg_type == "photo":
                    caption = welcome_data.get("caption", "")
                    caption_entities = welcome_data.get("caption_entities", [])
                    
                    if is_first and caption:
                        prefix = f"{user_name}, "
                        prefix_len = len(prefix.encode('utf-16-le')) // 2
                        adjusted_entities = []
                        for e in caption_entities:
                            e_copy = e.copy()
                            e_copy['offset'] += prefix_len
                            adjusted_entities.append(e_copy)
                        caption = prefix + caption
                        caption_entities = adjusted_entities
                    elif is_first and not caption:
                        caption = user_name
                        caption_entities = []

                    await context.bot.send_photo(
                        chat_id=user_id, 
                        photo=welcome_data["file_id"], 
                        caption=caption,
                        caption_entities=caption_entities
                    )

                elif msg_type == "document":
                    caption = welcome_data.get("caption", "")
                    caption_entities = welcome_data.get("caption_entities", [])
                    
                    if is_first and caption:
                        prefix = f"{user_name}, "
                        prefix_len = len(prefix.encode('utf-16-le')) // 2
                        adjusted_entities = []
                        for e in caption_entities:
                            e_copy = e.copy()
                            e_copy['offset'] += prefix_len
                            adjusted_entities.append(e_copy)
                        caption = prefix + caption
                        caption_entities = adjusted_entities
                    elif is_first and not caption:
                        caption = user_name
                        caption_entities = []

                    await context.bot.send_document(
                        chat_id=user_id,
                        document=welcome_data["file_id"],
                        caption=caption,
                        caption_entities=caption_entities
                    )

                elif msg_type == "voice":
                    caption = welcome_data.get("caption", "")
                    caption_entities = welcome_data.get("caption_entities", [])
                    
                    if is_first and caption:
                        prefix = f"{user_name}, "
                        prefix_len = len(prefix.encode('utf-16-le')) // 2
                        adjusted_entities = []
                        for e in caption_entities:
                            e_copy = e.copy()
                            e_copy['offset'] += prefix_len
                            adjusted_entities.append(e_copy)
                        caption = prefix + caption
                        caption_entities = adjusted_entities
                    elif is_first and not caption:
                        caption = user_name
                        caption_entities = []

                    await context.bot.send_voice(
                        chat_id=user_id,
                        voice=welcome_data["file_id"],
                        caption=caption,
                        caption_entities=caption_entities
                    )
            except Exception as e:
                print(f"Error sending sequence welcome message {index}: {e}")
    else:
        try:
            await context.bot.send_message(chat_id=user_id, text=f"Hello {user_name}!")
        except Exception as e:
            print(f"Error sending default text: {e}")

# --- 2. /setwelcome कमांड ---
async def set_welcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    message = update.message
    if message.reply_to_message:
        source_msg = message.reply_to_message
        welcome_data = {}
        
        if source_msg.text:
            welcome_data = {
                "type": "text",
                "text": source_msg.text,
                "entities": [e.to_dict() for e in source_msg.entities] if source_msg.entities else []
            }
        elif source_msg.photo:
            welcome_data = {
                "type": "photo",
                "file_id": source_msg.photo[-1].file_id,
                "caption": source_msg.caption or "",
                "caption_entities": [e.to_dict() for e in source_msg.caption_entities] if source_msg.caption_entities else []
            }
        elif source_msg.document:
            welcome_data = {
                "type": "document",
                "file_id": source_msg.document.file_id,
                "caption": source_msg.caption or "",
                "caption_entities": [e.to_dict() for e in source_msg.caption_entities] if source_msg.caption_entities else []
            }
        elif source_msg.voice:
            welcome_data = {
                "type": "voice",
                "file_id": source_msg.voice.file_id,
                "caption": source_msg.caption or "",
                "caption_entities": [e.to_dict() for e in source_msg.caption_entities] if source_msg.caption_entities else []
            }

        if welcome_data:
            welcome_list = get_saved_welcome_messages()
            welcome_list.append(welcome_data)
            with open(WELCOME_MSG_FILE, "w", encoding="utf-8") as f:
                json.dump(welcome_list, f, ensure_ascii=False)
            await message.reply_text(f"✨ प्रीमियम इमोजी और स्टाइल के साथ मैसेज जोड़ दिया गया है!\n📊 कुल सेट किए गए मैसेज: {len(welcome_list)}")
        else:
            await message.reply_text("❌ जिस मैसेज पर रिप्लाई किया है, उसमें टेक्स्ट, फोटो, फाइल या वॉइस नोट होना चाहिए।")
    else:
        await message.reply_text("❌ कृपया अपने उस मैसेज पर रिप्लाई करें जिसे जोड़ना है और लिखें: /setwelcome")

# --- 3. /clearwelcome कमांड ---
async def clear_welcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if os.path.exists(WELCOME_MSG_FILE):
        os.remove(WELCOME_MSG_FILE)
    await update.message.reply_text("🗑️ सभी वेलकम मैसेज डिलीट/रीसेट कर दिए गए हैं!")

# --- 4. टेक्स्ट ब्रॉडकास्ट कमांड ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("तू इस कमांड को इस्तेमाल नहीं कर सकता!")
        return

    message_text = " ".join(context.args)
    if not message_text:
        await update.message.reply_text("❌ कृपया मैसेज लिखें, जैसे: /broadcast आपका संदेश")
        return

    users = get_all_users()
    if users:
        success = 0
        failed = 0
        status_msg = await update.message.reply_text("📤 ब्रॉडकास्ट शुरू हो गया है...")
        
        for user_id in users:
            try:
                await context.bot.send_message(chat_id=user_id, text=message_text)
                success += 1
            except Exception as e:
                failed += 1
        
        await status_msg.edit_text(f"✅ ब्रॉडकास्ट पूरा हुआ!\n\n सफल: {success}\n असफल: {failed}")
    else:
        await update.message.reply_text("❌ कोई यूजर डेटाबेस नहीं मिला!")

# --- 5. एडमिन लाइव चैट और बाकी हैंडलर ---
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    if user.id == ADMIN_ID:
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
                    
                    await message.reply_text("✅ मैसेज यूजर को भेज दिया गया है!")
                except Exception as g:
                    await message.reply_text(f"❌ भेजने में एरर आया: {g}")
        return

    else:
        save_user(user.id)
        
        user_name = user.full_name
        username = f"@{user.username}" if user.username else "कोई यूजरनेम नहीं"
        
        forward_header = f"📩 नया मैसेज आया है!\n👤 नाम: {user_name}\n🔗 यूजरनेम: {username}\n🆔 User ID: {user.id}\n-------------------\n"
        
        try:
            if message.text:
                await context.bot.send_message(chat_id=ADMIN_ID, text=forward_header + message.text)
            elif message.voice:
                await context.bot.send_message(chat_id=ADMIN_ID, text=forward_header + "[नीचे यूजर का वॉइस नोट है]")
                await context.bot.send_voice(chat_id=ADMIN_ID, voice=message.voice.file_id)
            elif message.photo:
                await context.bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=forward_header + (message.caption or ""))
            else:
                await context.bot.send_message(chat_id=ADMIN_ID, text=forward_header + "[यूजर ने मीडिया भेजा है]")
        except Exception as e:
                print(f"Error forwarding to admin: {e}")

if __name__ == '__main__':
    keep_alive()
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(CommandHandler("setwelcome", set_welcome_command))
    app.add_handler(CommandHandler("clearwelcome", clear_welcome_command))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_messages))

    print("Bot started successfully...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
