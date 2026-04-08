from flask import Flask
import os
import threading
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# 🔹 Flask app
web = Flask(__name__)

@web.route('/')
def home():
    return "Bot is running!"

# 🔹 Config
TOKEN = "8656250844:AAGCxiFYQBzWvHGyZOFkHepHlUoumBm_RC4"
ADMIN_ID = 5328734113

main_menu = [
    ["📁 Text to VCF", "📄 VCF to Text"],
    ["🔄 Merge VCF", "📦 Split Text"],
    ["⚓ Admin/Navy", "💎 Buy Premium"],
]

user_state = {}

# 🔹 Load users
def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return {}

# 🔹 Save users
def save_users(data):
    with open("users.json", "w") as f:
        json.dump(data, f, indent=4)

# 🔹 Start
def start(update: Update, context: CallbackContext):
    users = load_users()
    uid = str(update.message.from_user.id)

    if uid not in users:
        users[uid] = {"premium": False}
        save_users(users)

    update.message.reply_text(
        "🔥 ULTRA PRO BOT 🔥",
        reply_markup=ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    )

# 🔹 TEXT HANDLER
def handle_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text

    # 🔥 MENU
    if text == "📁 Text to VCF":
        user_state[user_id] = {"mode": "txt_to_vcf"}
        update.message.reply_text("📤 Send TXT file")
        return

    if text == "📄 VCF to Text":
        user_state[user_id] = {"mode": "vcf_to_txt"}
        update.message.reply_text("📤 Send VCF file")
        return

    if text == "🔄 Merge VCF":
        update.message.reply_text("⚠️ Feature coming soon")
        return

    if text == "📦 Split Text":
        update.message.reply_text("⚠️ Feature coming soon")
        return

    if text == "⚓ Admin/Navy":
        if user_id == ADMIN_ID:
            users = load_users()
            update.message.reply_text(f"👥 Total Users: {len(users)}")
        else:
            update.message.reply_text("❌ Not allowed")
        return

    if text == "💎 Buy Premium":
        update.message.reply_text("📞 Contact admin for premium")
        return

    # 🔹 STEP PROCESS (TXT → VCF)
    state = user_state.get(user_id)

    if not state:
        update.message.reply_text("⚠️ Please select option first")
        return

    if state.get("mode") != "txt_to_vcf":
        return

    if state.get("step") == "name":
        state["name"] = text
        state["step"] = "prefix"
        update.message.reply_text("Enter file prefix:")
        return

    if state.get("step") == "prefix":
        state["prefix"] = text
        state["step"] = "limit"
        update.message.reply_text("Enter contacts per VCF:")
        return

    if state.get("step") == "limit":
        try:
            limit = int(text)
        except:
            update.message.reply_text("❌ Enter valid number")
            return

        state["limit"] = limit

        try:
            with open(state["file"]) as f:
                numbers = f.read().splitlines()
        except:
            update.message.reply_text("❌ File error, resend file")
            return

        chunks = [numbers[i:i+limit] for i in range(0, len(numbers), limit)]

        update.message.reply_text("⏳ Processing...")

        for idx, chunk in enumerate(chunks):
            vcf_data = ""
            for i, num in enumerate(chunk):
                vcf_data += "BEGIN:VCARD\nVERSION:3.0\n"
                vcf_data += f"FN:{state['prefix']} {state['name']} {i+1}\n"
                vcf_data += f"TEL;TYPE=CELL:{num}\nEND:VCARD\n"

            filename = f"{user_id}_{idx}.vcf"
            with open(filename, "w") as f:
                f.write(vcf_data)

            update.message.reply_document(open(filename, "rb"))
            os.remove(filename)

        update.message.reply_text("✅ Done")
        user_state.pop(user_id)

# 🔹 FILE HANDLER (UNIFIED)
def handle_files(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    file = update.message.document.get_file()
    filename = update.message.document.file_name.lower()

    state = user_state.get(user_id)

    if not state:
        update.message.reply_text("⚠️ Please select option first")
        return

    # 🔥 TXT → VCF
    if filename.endswith(".txt") and state.get("mode") == "txt_to_vcf":
        path = f"{user_id}.txt"
        file.download(path)

        user_state[user_id]["file"] = path
        user_state[user_id]["step"] = "name"

        update.message.reply_text("Enter Contact Name:")
        return

    # 🔥 VCF → TXT
    if filename.endswith(".vcf") and state.get("mode") == "vcf_to_txt":
        path = f"{user_id}.vcf"
        file.download(path)

        numbers = []

        try:
            with open(path, "r") as f:
                for line in f:
                    if line.startswith("TEL"):
                        num = line.split(":")[-1].strip()
                        numbers.append(num)
        except:
            update.message.reply_text("❌ File read error")
            return

        txt_file = f"{user_id}_output.txt"
        with open(txt_file, "w") as f:
            f.write("\n".join(numbers))

        update.message.reply_document(open(txt_file, "rb"))

        os.remove(path)
        os.remove(txt_file)
        return

    update.message.reply_text("❌ Wrong file for selected option")

# 🔹 ERROR HANDLER
def error(update, context):
    print(f"Error: {context.error}")

# 🔹 RUN BOT
def run_bot():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_files))
    dp.add_handler(MessageHandler(Filters.text, handle_text))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()

# 🔹 THREAD
threading.Thread(target=run_bot).start()

# 🔹 FLASK RUN
port = int(os.environ.get("PORT", 10000))
web.run(host="0.0.0.0", port=port)