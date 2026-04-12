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

    # 📁 TEXT TO VCF
    if text == "📁 Text to VCF":
        user_state[user_id] = {
            "mode": "collect",
            "numbers": []
        }

        update.message.reply_text(
            "📥 Send Contacts\n═══════◇◆◇═══════\n📂 Numbers / .txt / .xlsx\n\n✅ Finish Type → /done"
        )
        return

    # 📥 COLLECT NUMBERS
    if state and state.get("mode") == "collect" and text != "/done":
        nums = text.split()

        for n in nums:
            n = n.replace(" ", "").replace("-", "").replace("+", "")
            if n.isdigit() and len(n) >= 8:
                state["numbers"].append(n)


    # ✅ DONE
    if text == "/done" and state and state.get("mode") == "collect":
        if not state["numbers"]:
            update.message.reply_text("❌ No contacts added")
            return

        state["mode"] = "ask_name"
        update.message.reply_text("1️⃣ VCF File Name?\n(Example: Hongkong)")
        return

    # STEP 1
    if state and state.get("mode") == "ask_name":
        state["file_name"] = text
        state["mode"] = "ask_prefix"
        update.message.reply_text("2️⃣ Contact Name Prefix?\n(Example: Vikky Boss)")
        return

    # STEP 2
    if state and state.get("mode") == "ask_prefix":
        state["prefix"] = text
        state["mode"] = "ask_start_vcf"
        update.message.reply_text("3️⃣ VCF File Starting Number?\n(Example: 1)")
        return

    # STEP 3
    if state and state.get("mode") == "ask_start_vcf":
        state["vcf_start"] = int(text)
        state["mode"] = "ask_contact_start"
        update.message.reply_text("4️⃣ Contact Starting Number?\n(Example: 1)")
        return

    # STEP 4
    if state and state.get("mode") == "ask_contact_start":
        state["contact_start"] = int(text)
        state["mode"] = "ask_limit"
        update.message.reply_text("5️⃣ Contacts per VCF file?\n(Example: 50)")
        return

    # FINAL STEP
    if state and state.get("mode") == "ask_limit":
        limit = int(text)
        numbers = state["numbers"]

        update.message.reply_text(
            f"🚀 Generating VCF Files\n═══════◇◆◇═══════\n📊 Total Contacts: {len(numbers)}\n⚡ Status: Processing..."
        )

        chunks = [numbers[i:i+limit] for i in range(0, len(numbers), limit)]
        contact_counter = state["contact_start"]

        for idx, chunk in enumerate(chunks):
            vcf_data = ""

            for num in chunk:
                vcf_data += f"""BEGIN:VCARD
VERSION:3.0
FN:{state['prefix']} {contact_counter}
TEL;TYPE=CELL:{num}
END:VCARD
"""
                contact_counter += 1

            filename = f"{state['file_name']}{state['vcf_start'] + idx}.vcf"

            with open(filename, "w") as f:
                f.write(vcf_data)

            update.message.reply_document(open(filename, "rb"))
            os.remove(filename)

        update.message.reply_text("✅ VCF Generation Completed Successfully! 🎉")
        user_state.pop(user_id)
        return

    # 🔄 MERGE VCF
    if text == "🔄 Merge VCF":
        user_state[user_id] = {
            "mode": "merge_vcf",
            "step": "ask_filename"
        }
        update.message.reply_text("Enter output VCF file name:")
        return

    # merge filename
    if state and state.get("mode") == "merge_vcf" and state.get("step") == "ask_filename":
        state["filename"] = text
        state["step"] = "ask_prefix"
        update.message.reply_text("Enter contact name prefix:")
        return

    # merge prefix
    if state and state.get("mode") == "merge_vcf" and state.get("step") == "ask_prefix":
        state["prefix"] = text
        state["step"] = "collecting"
        state["all_numbers"] = []
        update.message.reply_text("📤 Send all VCF files, then type DONE")
        return

    # DONE merge
    if text == "DONE" and state and state.get("mode") == "merge_vcf":
        numbers = list(set(state.get("all_numbers", [])))

        if not numbers:
            update.message.reply_text("❌ No data found")
            return

        vcf_data = ""
        for i, num in enumerate(numbers):
            vcf_data += f"BEGIN:VCARD\nVERSION:3.0\nFN:{state['prefix']} {i+1}\nTEL;TYPE=CELL:{num}\nEND:VCARD\n"

        filename = f"{state['filename']}.vcf"

        with open(filename, "w") as f:
            f.write(vcf_data)

        update.message.reply_document(open(filename, "rb"))
        os.remove(filename)

        user_state.pop(user_id)
        update.message.reply_text("✅ All VCF merged")
        return

    # 📦 Split
    if text == "📦 Split Text":
        update.message.reply_text("Use Text to VCF feature")
        return

    # ADMIN
    if text == "⚓ Admin/Navy":
        if user_id == ADMIN_ID:
            users = load_users()
            update.message.reply_text(f"👥 Total Users: {len(users)}")
        else:
            update.message.reply_text("❌ Not allowed")
        return

    # PREMIUM
    if text == "💎 Buy Premium":
        update.message.reply_text("📞 Contact admin")
        return

    # DONE VCF → TXT
    if text == "/done" and state and state.get("mode") == "vcf_to_txt":
        if not state.get("numbers"):
            update.message.reply_text("❌ No files uploaded")
            return

        state["step"] = "ask_name"
        update.message.reply_text("📝 Enter file name:")
        return

    # NAME INPUT
    if state and state.get("mode") == "vcf_to_txt" and state.get("step") == "ask_name":
        filename = f"{text}.txt"

        with open(filename, "w") as f:
            f.write("\n".join(state["numbers"]))

        update.message.reply_document(open(filename, "rb"))
        os.remove(filename)

        user_state.pop(user_id)
        update.message.reply_text("✅ Extraction Completed")
        return

    # TXT → VCF steps
    if not state:
        update.message.reply_text("⚠️ Select option first")
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

        with open(state["file"]) as f:
            numbers = f.read().splitlines()

        chunks = [numbers[i:i+limit] for i in range(0, len(numbers), limit)]

        update.message.reply_text("⏳ Processing...")

        for idx, chunk in enumerate(chunks):
            vcf_data = ""
            for i, num in enumerate(chunk):
                vcf_data += f"BEGIN:VCARD\nVERSION:3.0\nFN:{state['prefix']} {state['name']} {i+1}\nTEL;TYPE=CELL:{num}\nEND:VCARD\n"

            filename = f"{state['prefix']}_{idx+1}.vcf"

            with open(filename, "w") as f:
                f.write(vcf_data)

            update.message.reply_document(open(filename, "rb"))
            os.remove(filename)

        update.message.reply_text("✅ Done")
        user_state.pop(user_id)

#file handler
def handle_files(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    file = update.message.document.get_file()
    filename = update.message.document.file_name.lower()

    state = user_state.get(user_id)

    if not state:
        update.message.reply_text("⚠️ Select option first")
        return

    path = f"{user_id}_{filename}"
    file.download(path)

    # ✅ TXT → VCF
    if filename.endswith(".txt") and state.get("mode") == "collect":
        with open(path) as f:
            for line in f:
                num = line.strip()

                # ✅ clean number
                num = num.replace(" ", "").replace("-", "").replace("+", "")

                if num.isdigit() and len(num) >= 8:
                    state["numbers"].append(num)

        os.remove(path)
        update.message.reply_text(
            f"📥 Collecting Contacts\n═══════◇◆◇═══════\n📊 Final Added: {len(state['numbers'])}\n✅ Finished!"
        )
        return

    # ✅ VCF → TXT
    if filename.endswith(".vcf") and state.get("mode") == "vcf_to_txt":
        with open(path) as f:
            for line in f:
                if line.startswith("TEL"):
                    num = line.split(":")[-1].strip()
                    state["numbers"].append(num)

        os.remove(path)
        return

    # ✅ MERGE VCF
    if filename.endswith(".vcf") and state.get("mode") == "merge_vcf":
        if "all_numbers" not in state:
            state["all_numbers"] = []

        with open(path) as f:
            for line in f:
                if line.startswith("TEL"):
                    num = line.split(":")[-1].strip()
                    state["all_numbers"].append(num)

        os.remove(path)
        return

    # ❌ LAST me rakho
    update.message.reply_text("❌ Invalid file type")

# 🔹 ERROR
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

# 🔹 THREAD
threading.Thread(target=run_bot).start()

# 🔹 RUN FLASK
port = int(os.environ.get("PORT", 10000))
web.run(host="0.0.0.0", port=port)