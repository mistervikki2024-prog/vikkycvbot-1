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

# 🔹 Bot config
TOKEN = "8656250844:AAGCxiFYQBzWvHGyZOFkHepHlUoumBm_RC4"
ADMIN_ID = 5328734113

main_menu = [
    ["📁 Text to VCF", "📄 VCF to Text"],
    ["🔄 Merge VCF", "📦 Split Text"],
    ["⚓ Admin/Navy", "💎 Buy Premium"],
]

user_state = {}
vcf_data = {}

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

# 🔹 Start command
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

# 🔹 Handle TXT file
def handle_document(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    file = update.message.document.get_file()
    filename = update.message.document.file_name

    if not filename.endswith(".txt"):
        update.message.reply_text("❌ Please send TXT file only")
        return

    path = f"{user_id}.txt"
    file.download(path)

    user_state[user_id] = {"step": "name", "file": path}
    update.message.reply_text("Enter Contact Name:")

def handle_vcf(update, context):
    user_id = update.message.from_user.id

    if user_id not in vcf_data:
        return

    file = update.message.document
    if not file.file_name.endswith(".vcf"):
        update.message.reply_text("❌ Only .vcf file allowed")
        return

    tg_file = file.get_file()
    path = f"{user_id}_{len(vcf_data[user_id]['files'])}.vcf"
    tg_file.download(path)

    vcf_data[user_id]["files"].append(path)

    # Extract numbers
    total_numbers = 0
    for f in vcf_data[user_id]["files"]:
        with open(f, encoding="utf-8", errors="ignore") as file:
            for line in file:
                if "TEL" in line:
                    total_numbers += 1

    update.message.reply_text(
        f"📄 Extracting Numbers\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📁 Files Uploaded: {len(vcf_data[user_id]['files'])}\n"
        f"📊 Extracted: {total_numbers}\n"
        f"⏳ Status: Scanning...\n\n"
        f"📂 Keep sending files\n"
        f"✅ Finish Type → /done"
    )

def handle_vcf(update, context):
    user_id = update.message.from_user.id

    if user_id not in vcf_data:
        return

    file = update.message.document
    if not file.file_name.endswith(".vcf"):
        update.message.reply_text("❌ Only .vcf file allowed")
        return

    tg_file = file.get_file()
    path = f"{user_id}_{len(vcf_data[user_id]['files'])}.vcf"
    tg_file.download(path)

    vcf_data[user_id]["files"].append(path)

    # Extract numbers
    total_numbers = 0
    for f in vcf_data[user_id]["files"]:
        with open(f, encoding="utf-8", errors="ignore") as file:
            for line in file:
                if "TEL" in line:
                    total_numbers += 1

    update.message.reply_text(
        f"📄 Extracting Numbers\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📁 Files Uploaded: {len(vcf_data[user_id]['files'])}\n"
        f"📊 Extracted: {total_numbers}\n"
        f"⏳ Status: Scanning...\n\n"
        f"📂 Keep sending files\n"
        f"✅ Finish Type → /done"
    )

def done(update, context):
    user_id = update.message.from_user.id

    if user_id not in vcf_data:
        update.message.reply_text("❌ No files uploaded")
        return

    user_state[user_id] = {"step": "vcf_name"}
    update.message.reply_text(
        "📝 Enter the name for your .txt file:\nExample: ExtractedList"
    )

# 🔹 Handle text steps
def handle_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text
    if text == "📄 VCF to Text":
        vcf_data[user_id] = {"files": []}

        update.message.reply_text(
            "📤 Upload VCF Files\n"
            "━━━━━━━━━━━━━━━\n"
            "📁 Send one or multiple .vcf files\n"
            "✅ Finish Type → /done"
        )
        return

    if text == "📁 Text to VCF":
        update.message.reply_text("Send TXT file")
        return

    state = user_state.get(user_id)
    if not state:
        update.message.reply_text("Send TXT file first")
        return

    if state["step"] == "name":
        state["name"] = text
        state["step"] = "prefix"
        update.message.reply_text("Enter VCF file name:")
        return

    if state["step"] == "prefix":
        state["prefix"] = text
        state["step"] = "limit"
        update.message.reply_text("Enter contacts per VCF:")
        return

    if state["step"] == "limit":
        try:
            limit = int(text)
        except:
            update.message.reply_text("Enter valid number")
            return

        state["limit"] = limit

        with open(state["file"]) as f:
            numbers = f.read().splitlines()

        chunks = [numbers[i:i+limit] for i in range(0, len(numbers), limit)]

        for idx, chunk in enumerate(chunks):
            vcf = ""
            for i, num in enumerate(chunk):
                vcf += "BEGIN:VCARD\nVERSION:3.0\n"
                vcf += f"FN:{state['prefix']} {state['name']} {i+1}\n"
                vcf += f"TEL;TYPE=CELL:{num}\nEND:VCARD\n"

            filename = f"{state['prefix']}_{idx+1}.vcf"
            with open(filename, "w") as f:
                f.write(vcf)

            update.message.reply_document(open(filename, "rb"))
            os.remove(filename)

        update.message.reply_text("✅ Done")
        user_state.pop(user_id)

    state = user_state.get(user_id)
    if state and state.get("step") == "vcf_name":
        filename = text + ".txt"
        numbers = []

    for f in vcf_data[user_id]["files"]:
        with open(f, encoding="utf-8", errors="ignore") as file:
            for line in file:
                if "TEL" in line:
                    num = line.split(":")[-1].strip()
                    numbers.append(num)

    with open(filename, "w") as f:
        f.write("✅ Extracted Numbers\n\n")
        for n in numbers:
            f.write(n + "\n")

    update.message.reply_document(open(filename, "rb"))
    os.remove(filename)

    update.message.reply_text("✅ Extraction Completed Successfully! 🎉")

    # cleanup
    for f in vcf_data[user_id]["files"]:
        os.remove(f)

    vcf_data.pop(user_id)
    user_state.pop(user_id)
    return

# 🔹 Run bot
def run_bot():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_document))
    dp.add_handler(MessageHandler(Filters.text, handle_text))

    updater.start_polling()
    updater.idle()

# 🔹 Start bot thread
threading.Thread(target=run_bot).start()

# 🔹 Run Flask
port = int(os.environ.get("PORT", 10000))
web.run(host="0.0.0.0", port=port)