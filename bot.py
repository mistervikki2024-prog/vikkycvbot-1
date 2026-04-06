from flask import Flask
import os
import threading
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# -------------------- Flask --------------------
web = Flask(__name__)

@web.route('/')
def home():
    return "Bot is running!"

# -------------------- Bot Config --------------------
TOKEN = "8656250844:AAGCxiFYQBzWvHGyZOFkHepHlUoumBm_RC4"
ADMIN_ID = 5328734113

main_menu = [
    ["📁 Text to VCF", "📄 VCF to Text"],
    ["🔄 Merge VCF", "📦 Split Text"],
    ["⚓ Admin/Navy", "💎 Buy Premium"],
]

user_state = {}
vcf_data = {}

# -------------------- Users --------------------
def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open("users.json", "w") as f:
        json.dump(data, f, indent=4)

# -------------------- Start --------------------
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

# -------------------- TXT → VCF --------------------
def handle_txt(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if not update.message.document:
        update.message.reply_text("❌ Please send a valid TXT file")
        return

    file = update.message.document.get_file()
    filename = update.message.document.file_name

    if not filename.endswith(".txt"):
        update.message.reply_text("❌ Please send TXT file only")
        return

    path = f"{user_id}.txt"
    file.download(path)

    user_state[user_id] = {"step": "name", "file": path}
    update.message.reply_text("Step 1️⃣ Enter Contact Name:")

# -------------------- VCF → TXT --------------------
def handle_vcf(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    state = user_state.get(user_id)

    if not state or state.get("step") != "upload":
        return

    if not update.message.document or not update.message.document.file_name.endswith(".vcf"):
        update.message.reply_text("❌ Only .vcf file allowed")
        return

    file = update.message.document.get_file()
    path = f"{user_id}_{len(vcf_data[user_id]['files'])}.vcf"
    file.download(path)
    vcf_data[user_id]["files"].append(path)

    total = 0
    for f in vcf_data[user_id]["files"]:
        with open(f, encoding="utf-8", errors="ignore") as ff:
            total += sum(1 for line in ff if line.startswith("TEL"))

    update.message.reply_text(
        f"📄 Extracting Numbers\n━━━━━━━━━━━━━━━\n"
        f"📁 Files Uploaded: {len(vcf_data[user_id]['files'])}\n"
        f"📊 Extracted: {total}\n"
        f"⏳ Status: Scanning...\n\n"
        f"📂 Keep sending files\n"
        f"✅ Finish Type → /done"
    )

# -------------------- All Documents Handler --------------------
def handle_all_documents(update: Update, context: CallbackContext):
    file_name = update.message.document.file_name.lower()
    if file_name.endswith(".txt"):
        handle_txt(update, context)
    elif file_name.endswith(".vcf"):
        handle_vcf(update, context)
    else:
        update.message.reply_text("❌ Invalid file type!")

# -------------------- Menu & Text Handler --------------------
def handle_all_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text
    state = user_state.get(user_id)

    # --- Menu ---
    if text == "📁 Text to VCF":
        update.message.reply_text("Send TXT file")
        return
    if text == "📄 VCF to Text":
        vcf_data[user_id] = {"files": []}
        user_state[user_id] = {"step": "upload"}
        update.message.reply_text(
            "📤 Upload VCF Files\n━━━━━━━━━━━━━━━\n"
            "📁 Send one or multiple .vcf files\n"
            "✅ Finish Type → /done"
        )
        return

    # --- TXT → VCF Steps ---
    if state and state.get("step") in ["name", "prefix", "limit"]:
        if state["step"] == "name":
            state["name"] = text
            state["step"] = "prefix"
            update.message.reply_text("Step 2️⃣ Enter file prefix:")
            return

        if state["step"] == "prefix":
            state["prefix"] = text
            state["step"] = "limit"
            update.message.reply_text("Step 3️⃣ Enter contacts per VCF:")
            return

        if state["step"] == "limit":
            try:
                limit = int(text)
            except:
                update.message.reply_text("Enter valid number")
                return

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

            update.message.reply_text("✅ Text to VCF Done!")
            user_state.pop(user_id)
            os.remove(state["file"])
            return

    # --- TXT filename after VCF extraction ---
    if state and state.get("step") == "txt_name":
        filename = text + ".txt"
        numbers = []

        for f in vcf_data[user_id]["files"]:
            with open(f, encoding="utf-8", errors="ignore") as ff:
                for line in ff:
                    if line.startswith("TEL"):
                        numbers.append(line.split(":")[-1].strip())

        with open(filename, "w") as f:
            f.write("✅ Extracted Numbers\n━━━━━━━━━━━━━━━\n")
            for n in numbers:
                f.write(n + "\n")

        update.message.reply_document(open(filename, "rb"))
        update.message.reply_text("✅ Extraction Completed Successfully! 🎉")

        # cleanup
        for f in vcf_data[user_id]["files"]:
            os.remove(f)
        os.remove(filename)

        vcf_data.pop(user_id)
        user_state.pop(user_id)
        return

# -------------------- Done --------------------
def done(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if user_id not in vcf_data or not vcf_data[user_id]["files"]:
        update.message.reply_text("❌ No files uploaded")
        return

    user_state[user_id] = {"step": "txt_name"}
    update.message.reply_text(
        "📝 Enter the name for your .txt file:\nExample: ExtractedList"
    )

# -------------------- Run Bot --------------------
def run_bot():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("done", done))

    dp.add_handler(MessageHandler(Filters.document & ~Filters.command, handle_all_documents))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_all_text))

    updater.start_polling()
    updater.idle()

# -------------------- Main --------------------
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port, threaded=True)