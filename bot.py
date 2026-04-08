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
    ["Manual VCF"],
    ["🔄 Merge VCF", "📦 Split Text"],
    ["Get CTC Name", "My Subscription"],
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
    state = user_state.get(user_id)

    if text == "📁 Text to VCF":
        user_state[user_id] = {"mode": "txt_to_vcf"}
        update.message.reply_text("📤 Send TXT file")
        return

    if text == "📄 VCF to Text":
        user_state[user_id] = {"mode": "vcf_to_txt", "step": "waiting_file"}
        update.message.reply_text("📤 Send VCF file(s)")
        return

    if text == "🔄 Merge VCF":
        user_state[user_id] = {"mode": "merge_vcf", "step": "ask_filename"}
        update.message.reply_text("Enter output VCF file name:")
        return

    if state and state.get("mode") == "merge_vcf" and state.get("step") == "ask_filename":
        state["filename"] = text
        state["step"] = "ask_prefix"
        update.message.reply_text("Enter contact name prefix:")
        return

    if state and state.get("mode") == "merge_vcf" and state.get("step") == "ask_prefix":
        state["prefix"] = text
        state["step"] = "collecting"
        state["all_numbers"] = []
        update.message.reply_text("📤 Send VCF files. Type DONE when finished.")
        return

    if text == "DONE" and state and state.get("mode") == "merge_vcf":
        numbers = list(set(state.get("all_numbers", [])))

        if not numbers:
            update.message.reply_text("❌ No data found")
            return

        vcf_data = ""
        for i, num in enumerate(numbers):
            vcf_data += "BEGIN:VCARD\nVERSION:3.0\n"
            vcf_data += f"FN:{state['prefix']} {i+1}\n"
            vcf_data += f"TEL;TYPE=CELL:{num}\nEND:VCARD\n"

        filename = f"{state['filename']}.vcf"

        with open(filename, "w") as f:
            f.write(vcf_data)

        update.message.reply_document(open(filename, "rb"))
        os.remove(filename)
        user_state.pop(user_id)

        update.message.reply_text("✅ Merged")
        return

    if text == "📦 Split Text":
        update.message.reply_text("Use Text to VCF feature")
        return

    if text == "⚓ Admin/Navy":
        if user_id == ADMIN_ID:
            users = load_users()
            update.message.reply_text(f"👥 Users: {len(users)}")
        else:
            update.message.reply_text("❌ Not allowed")
        return

    if text == "💎 Buy Premium":
        update.message.reply_text("📞 Contact admin")
        return

    if state and state.get("mode") == "vcf_to_txt" and state.get("step") == "ask_name":
        state["txt_name"] = text
        state["step"] = "collecting"
        state["all_numbers"] = []
        update.message.reply_text("Send VCF files then DONE")
        return

    if text == "DONE" and state and state.get("mode") == "vcf_to_txt":
        numbers = state.get("all_numbers", [])

        if not numbers:
            update.message.reply_text("❌ No numbers")
            return

        filename = f"{state['txt_name']}.txt"

        with open(filename, "w") as f:
            f.write("\n".join(numbers))

        update.message.reply_document(open(filename, "rb"))
        os.remove(filename)
        user_state.pop(user_id)

        update.message.reply_text("✅ Done")
        return

    if not state:
        update.message.reply_text("⚠️ Select option first")
        return

    if state.get("mode") != "txt_to_vcf":
        return

    if state.get("step") == "name":
        state["name"] = text
        state["step"] = "prefix"
        update.message.reply_text("Enter prefix:")
        return

    if state.get("step") == "prefix":
        state["prefix"] = text
        state["step"] = "limit"
        update.message.reply_text("Enter limit:")
        return

    if state.get("step") == "limit":
        try:
            limit = int(text)
        except:
            update.message.reply_text("❌ Number only")
            return

        numbers = open(state["file"]).read().splitlines()
        chunks = [numbers[i:i+limit] for i in range(0, len(numbers), limit)]

        for idx, chunk in enumerate(chunks):
            vcf = ""
            for i, num in enumerate(chunk):
                vcf += f"BEGIN:VCARD\nVERSION:3.0\nFN:{state['prefix']} {state['name']} {i+1}\nTEL:{num}\nEND:VCARD\n"

            fname = f"{state['prefix']}_{idx+1}.vcf"
            open(fname, "w").write(vcf)
            update.message.reply_document(open(fname, "rb"))
            os.remove(fname)

        user_state.pop(user_id)
        update.message.reply_text("✅ Done")

# 🔹 FILE HANDLER (FIXED)
def handle_files(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    file = update.message.document.get_file()
    filename = update.message.document.file_name.lower()

    state = user_state.get(user_id)

    if not state:
        update.message.reply_text("⚠️ Select option first")
        return

    # TXT → VCF
    if filename.endswith(".txt") and state.get("mode") == "txt_to_vcf":
        path = f"{user_id}.txt"
        file.download(path)

        state["file"] = path
        state["step"] = "name"

        update.message.reply_text("Enter Contact Name:")
        return

    # VCF → TXT
    elif filename.endswith(".vcf") and state.get("mode") == "vcf_to_txt":

        path = f"{user_id}_{filename}"
        file.download(path)

        if "all_numbers" not in state:
            state["all_numbers"] = []

        with open(path) as f:
            for line in f:
                if line.startswith("TEL"):
                    state["all_numbers"].append(line.split(":")[-1].strip())

        os.remove(path)

        if "txt_name" not in state:
            state["step"] = "ask_name"
            update.message.reply_text("Enter TXT name")

        return

    # MERGE VCF
    elif filename.endswith(".vcf") and state.get("mode") == "merge_vcf":

        path = f"{user_id}_{filename}"
        file.download(path)

        if "all_numbers" not in state:
            state["all_numbers"] = []

        with open(path) as f:
            for line in f:
                if line.startswith("TEL"):
                    state["all_numbers"].append(line.split(":")[-1].strip())

        os.remove(path)
        return

    else:
        update.message.reply_text("❌ Wrong file")

# 🔹 ERROR HANDLER
def error(update, context):
    print("Error:", context.error)

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

threading.Thread(target=run_bot).start()

port = int(os.environ.get("PORT", 10000))
web.run(host="0.0.0.0", port=port)