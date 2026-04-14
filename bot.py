from flask import Flask
import os
import threading
import json
import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

def progress_bar(current, total):
    percent = int((current / total) * 100) if total else 0
    filled = int(percent / 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"{bar} {percent}%"

# 🔹 Flask app
web = Flask(__name__)

@web.route('/')
def home():
    return "Bot is running!"

# 🔹 Config
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5328734113"))

main_menu = [
    ["Text to VCF,icon_custom_emoji_id="6069143072510318877", "VCF to Text,icon_custom_emoji_id="6069143072510318877"],
    ["📄 Manual VCF", "📁 Manual Text"],
    ["🔄 Merge VCF", "✂️ Split Text"],
    ["✍️ VCF Editer", "💳 My Subscription"],
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
            "numbers": [],
            "files": 0,
            "start_time": time.time()
        }

        update.message.reply_text(
            "📥 Send Contacts\n═══════════════\n📂 Numbers / .txt / .xlsx\n\n✅ Finish Type → /done"
        )
        return

    # 📄 VCF TO TEXT
    if text == "📄 VCF to Text":
        user_state[user_id] = {
            "mode": "vcf_to_txt",
            "numbers": [],
            "files": 0,
            "msg_id": None,
            "start_time": time.time(),
            "user_total_files": None,
            "total_lines": 0,
            "processed_lines": 0,
        }

        update.message.reply_text(
            "📤 Upload VCF Files\n━━━━━━━━━━━━━━━\n📁 Send one or multiple .vcf files\n\n✅ Finish Type → /done"
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
            f"🚀 Generating VCF Files\n━━━━━━━━━━━━━━━\n📊 Total Contacts: {len(numbers)}\n⚡ Status: Processing..."
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
        state["animating"] = False

        final_text = (
            f"📄 Final Result\n━━━━━━━━━━━━━━━\n"
            f"📁 Files Processed: {state.get('files', 0)}\n"
            f"📊 Total Extracted: {len(state['numbers'])}\n"
            f"✅ Finished!"
        )

        # ✅ EDIT MESSAGE (if exists)
        if state.get("msg_id"):
            context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=state["msg_id"],
                text=final_text
            )
        else:
            update.message.reply_text(final_text)

        state["step"] = "ask_name"

        update.message.reply_text(
            "📝 Enter the name for your .txt file:\nExample: ExtractedList"
        )
        return

# NAME INPUT
# NAME INPUT
    if state and state.get("mode") == "vcf_to_txt" and state.get("step") == "ask_name":
        filename = f"{text}.txt"

        with open(filename, "w") as f:
            f.write("\n".join(state["numbers"]))

        # 📄 Send file with ONLY caption
        update.message.reply_document(
            document=open(filename, "rb"),
            caption="✅ Extracted Numbers"
        )

        # 🎉 Only this reply
        update.message.reply_text("🎉 Extraction Completed Successfully!")

        os.remove(filename)
        user_state.pop(user_id)


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

def animate_progress(context, chat_id, msg_id, state):
    last_done = 0
    last_time = time.time()

    while state.get("animating"):
        time.sleep(0.5)

        total = max(state.get("total_lines", 1), 1)
        done = state.get("processed_lines", 0)

        # ✅ REAL SPEED (last 0.5 sec ka)
        now = time.time()
        speed = (done - last_done) / (now - last_time) if (now - last_time) > 0 else 0
        last_done = done
        last_time = now

        percent = min(int((done / total) * 100), 100)

        filled = int(percent / 5)
        bar = "█" * filled + "░" * (20 - filled)

        text_msg = (
            f"🔎 VCF SCANNING\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"📁 Files: {state.get('files', 0)}\n"
            f"📊 Extracted: {len(state.get('numbers', []))}\n\n"
            f"📈 Progress: {bar} {percent}%\n\n"
            f"⚡ Speed: {speed:.0f} lines/sec\n"
            f"🔄 {done}/{total} lines"
            f"Finish Type: /done"
        )

        try:
            context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text_msg
            )
        except:
            pass

def process_vcf_file(path, state):
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            state["total_lines"] += 1

            line = line.strip()

            if "TEL" in line.upper():
                num = line.split(":")[-1].strip()
                num = num.replace(" ", "").replace("-", "").replace("+", "")

                if num.isdigit() and len(num) >= 8:
                    state["numbers"].append(num)

            state["processed_lines"] += 1

    os.remove(path)

# 🔹 FILE HANDLER
def handle_files(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    file = update.message.document.get_file()
    filename = update.message.document.file_name.lower()

    state = user_state.get(user_id)
    # 👉 file count
    if state and state.get("mode") == "vcf_to_txt":
        state["files"] = state.get("files", 0) + 1


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

                num = num.replace(" ", "").replace("-", "").replace("+", "")

                if num.isdigit() and len(num) >= 8:
                    state["numbers"].append(num)

        os.remove(path)

        update.message.reply_text(
            f"📥 Collecting Contacts\n━━━━━━━━━━━━━━━\n📊 Final Added: {len(state['numbers'])}\n✅ Finished!"
        )
        return

    # ✅ XLSX → VCF
    if filename.endswith(".xlsx") and state.get("mode") == "collect":
        from openpyxl import load_workbook

        wb = load_workbook(path)
        sheet = wb.active

        for row in sheet.iter_rows(values_only=True):
            for cell in row:
                if cell:
                    num = str(cell).strip()

                    num = num.replace(" ", "").replace("-", "").replace("+", "")

                    if num.isdigit() and len(num) >= 8:
                        state["numbers"].append(num)

        os.remove(path)

        update.message.reply_text(
            f"📥 Collecting Contacts\n━━━━━━━━━━━━━━━\n📊 Final Added: {len(state['numbers'])}\n✅ Finished!"
        )
        return

# ✅ VCF → TXT (SINGLE MESSAGE MODE)
    if filename.endswith(".vcf") and state.get("mode") == "vcf_to_txt":

    # 👉 start animation (only once)
        if not state.get("msg_id"):
            msg = update.message.reply_text("📄 Starting...")
            state["msg_id"] = msg.message_id
            state["animating"] = True
            state["total_lines"] = 0
            state["processed_lines"] = 0

            threading.Thread(
                target=animate_progress,
                args=(context, update.message.chat_id, msg.message_id, state),
                daemon=True
                ).start()

    # 👉 process EVERY file
        threading.Thread(
            target=process_vcf_file,
            args=(path, state),
            daemon=True
            ).start()

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

    # ❌ INVALID FILE
    os.remove(path)
    update.message.reply_text("❌ Invalid file type")

# 🔹 ERROR
def error(update, context):
    print("Error:", context.error)

# 🔹 RUN BOT
def run_bot():
    print("Bot is starting")

    if not TOKEN:
        print("BOT_TOKEN missing")
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, handle_files))
    dp.add_handler(MessageHandler(Filters.text, handle_text))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


threading.Thread(target=run_bot).start()