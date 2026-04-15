import telebot
import re
import time
from io import BytesIO
from telebot import types

# ================= CONFIGURATION =================
TOKEN = "8656250844:AAGCxiFYQBzWvHGyZOFkHepHlUoumBm_RC4"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# In-memory dictionary to store user states and data
user_data = {}

# ================= HELPER FUNCTIONS =================
def extract_numbers(text):
    return re.findall(r'\b\d{7,15}\b', text)

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(
        types.KeyboardButton("Text to VCF", style="primary",icon_custom_emoji_id="5433653135799228968"),
        types.KeyboardButton("VCF to Text", style="primary",icon_custom_emoji_id="5431736674147114227")
    )
    return kb

# ================= COMMANDS =================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    user_data[uid] = {'state': 'IDLE'}
    
    # 💻 HACKER STYLE LOADING ANIMATION
    load_msg = bot.send_message(uid, "<code>[>_] SYSTEM INITIATED...\nEstablishing Secure Connection...\n[██░░░░░░░░] 20%</code>")
    time.sleep(0.4) 
    bot.edit_message_text("<code>[>_] BYPASSING PROTOCOLS...\nDecrypting VCF Modules...\n[███████░░░] 70%</code>", chat_id=uid, message_id=load_msg.message_id)
    time.sleep(0.4)
    bot.edit_message_text("<code>[>_] ACCESS GRANTED.\nDeploying Engine...\n[██████████] 100%</code>", chat_id=uid, message_id=load_msg.message_id)
    time.sleep(0.3)
    
    try: bot.delete_message(chat_id=uid, message_id=load_msg.message_id)
    except: pass

    # 💎 CLEAN & PROFESSIONAL WELCOME MESSAGE
    welcome = (
        "🔥 <b>WELCOME TO VCF CONVERTER BOT</b> 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<code>[+] Status: Online & Ready</code>\n"
        "<code>[+] Mode: Open Source Engine</code>\n\n"
        "👇 <i>Select a service from the menu below:</i>"
    )
    
    bot.send_message(uid, welcome, reply_markup=main_menu())

# ================= SERVICE ROUTER =================
@bot.message_handler(func=lambda m: m.text in ["Text to VCF", "VCF to Text"])
def service_router(message):
    uid = message.chat.id
    txt = message.text
    
    if "Text to VCF" in txt:
        user_data[uid] = {'state': 'COLLECT_T2V', 'nums': [], 'msg_id': None}
        bot.send_message(uid, "📥 <b>Send Contacts</b>\n━━━━━━━━━━━━━━━\n📂 Send Numbers or a Text File\n\n✅ Finish Type → <code>/done</code>", reply_markup=types.ReplyKeyboardRemove())
        
    elif "VCF to Text" in txt:
        user_data[uid] = {'state': 'COLLECT_V2T', 'nums': [], 'msg_id': None}
        bot.send_message(uid, "📤 <b>Upload VCF Files</b>\n━━━━━━━━━━━━━━━\n📁 Send one or multiple <b>.vcf</b> files\n\n✅ Finish Type → <code>/done</code>", reply_markup=types.ReplyKeyboardRemove())

# ================= UNIVERSAL HANDLER (WORKFLOW) =================
@bot.message_handler(content_types=['text', 'document'])
def universal_handler(message):
    uid = message.chat.id
    if uid not in user_data: return
    
    state = user_data[uid].get('state', 'IDLE')
    txt = message.text.strip() if message.text else ""

    if txt.lower() == '/cancel':
        user_data[uid] = {'state': 'IDLE'}
        return bot.send_message(uid, "❌ <b>Operation Cancelled.</b>", reply_markup=main_menu())

    extracted = []
    file_content = b""
    is_vcf = False
    
    # Extract data from Document or Text
    if message.document:
        try:
            file_info = bot.get_file(message.document.file_id)
            file_content = bot.download_file(file_info.file_path)
            extracted = extract_numbers(file_content.decode('utf-8', errors='ignore'))
            if message.document.file_name.endswith('.vcf'): is_vcf = True
        except: pass
    elif txt and txt.lower() != '/done':
        extracted = extract_numbers(txt)

# ---------------------------------------------------------
    # 1️⃣ TEXT TO VCF WORKFLOW
    # ---------------------------------------------------------
    if state == 'COLLECT_T2V':
        if txt.lower() == '/done':
            total = len(user_data[uid]['nums'])
            if total == 0: return bot.send_message(uid, "❌ No contacts collected.", reply_markup=main_menu())
            bot.send_message(uid, f"✅ <b>Collected {total} numbers.</b>")
            user_data[uid]['state'] = 'T2V_STEP_1'
            return bot.send_message(uid, "1️⃣ <b>VCF File Name?</b>\n(Example: <code>TargetData</code>)")

        user_data[uid]['nums'].extend(extracted)
        total = len(user_data[uid]['nums'])
        
        # Live updating message
        msg_text = f"📥 <b>Collecting Contacts</b>\n━━━━━━━━━━━━━━━\n📊 Total Added: <code>{total}</code>\n⏳ <i>Status: Processing...</i>\n\n📂 <i>Keep sending files/numbers</i>\n✅ Finish Type → <code>/done</code>"
        if not user_data[uid].get('msg_id'):
            msg = bot.send_message(uid, msg_text)
            user_data[uid]['msg_id'] = msg.message_id
        else:
            try: bot.edit_message_text(msg_text, chat_id=uid, message_id=user_data[uid]['msg_id'])
            except: pass

    elif state == 'T2V_STEP_1':
        user_data[uid]['vname'] = txt
        user_data[uid]['state'] = 'T2V_STEP_2'
        bot.send_message(uid, "2️⃣ <b>Contact Name Prefix?</b>\n(Example: <code>Hacker</code>)")
        
    elif state == 'T2V_STEP_2':
        user_data[uid]['prefix'] = txt
        user_data[uid]['state'] = 'T2V_STEP_3'
        bot.send_message(uid, "3️⃣ <b>VCF File Starting Number?</b>\n(Example: <code>1</code>)")
        
    elif state == 'T2V_STEP_3':
        user_data[uid]['vstart'] = int(txt) if txt.isdigit() else 1
        user_data[uid]['state'] = 'T2V_STEP_4'
        bot.send_message(uid, "4️⃣ <b>Contact Starting Number?</b>\n(Example: <code>1</code>)")
        
    elif state == 'T2V_STEP_4':
        user_data[uid]['cstart'] = int(txt) if txt.isdigit() else 1
        user_data[uid]['state'] = 'T2V_STEP_5'
        bot.send_message(uid, "5️⃣ <b>Contacts per VCF file?</b>\n(Example: <code>50</code>)")
        
    elif state == 'T2V_STEP_5':
        limit = int(txt) if txt.isdigit() else 50
        d = user_data[uid]
        nums = list(dict.fromkeys(d['nums'])) # Remove duplicates
        v_idx, c_idx = d['vstart'], d['cstart']
        
        bot.send_message(uid, f"🚀 <b>Generating VCF Files...</b>\n📊 Total Unique Contacts: <code>{len(nums)}</code>")
        
        for i in range(0, len(nums), limit):
            chunk = nums[i:i + limit]
            fname = f"{d['vname']}{v_idx}.vcf" if len(nums) > limit else f"{d['vname']}.vcf"
            vcf_str = ""
            for n in chunk:
                vcf_str += f"BEGIN:VCARD\nVERSION:3.0\nFN:{d['prefix']} {c_idx}\nTEL;TYPE=CELL:{n}\nEND:VCARD\n"
                c_idx += 1
            
            bio = BytesIO(vcf_str.encode('utf-8'))
            bio.name = fname
            bot.send_document(uid, bio)
            v_idx += 1
            
        bot.send_message(uid, "✅ <b>VCF Generation Completed Successfully!</b> 🎉", reply_markup=main_menu())
        user_data[uid] = {'state': 'IDLE'}

    # ---------------------------------------------------------
    # 2️⃣ VCF TO TEXT WORKFLOW
    # ---------------------------------------------------------
    elif state == 'COLLECT_V2T':
        if txt.lower() == '/done':
            total = len(user_data[uid]['nums'])
            if total == 0: return bot.send_message(uid, "❌ No VCFs collected.", reply_markup=main_menu())
            bot.send_message(uid, f"✅ <b>Extracted {total} numbers.</b>")
            user_data[uid]['state'] = 'V2T_NAME'
            return bot.send_message(uid, "📝 <b>Enter the name for your .txt file:</b>\n<i>Example: <code>ExtractedList</code></i>")

        user_data[uid]['nums'].extend(extracted)
        total = len(user_data[uid]['nums'])
        
        msg_text = f"📄 <b>Extracting Numbers</b>\n━━━━━━━━━━━━━━━\n📊 Extracted: <code>{total}</code>\n⏳ <i>Status: Scanning...</i>\n\n📂 <i>Keep sending VCF files</i>\n✅ Finish Type → <code>/done</code>"
        if not user_data[uid].get('msg_id'):
            msg = bot.send_message(uid, msg_text)
            user_data[uid]['msg_id'] = msg.message_id
        else:
            try: bot.edit_message_text(msg_text, chat_id=uid, message_id=user_data[uid]['msg_id'])
            except: pass

    elif state == 'V2T_NAME':
        nums = list(dict.fromkeys(user_data[uid]['nums'])) # Remove duplicates
        bio = BytesIO("\n".join(nums).encode('utf-8'))
        bio.name = txt + ".txt" if not txt.endswith('.txt') else txt
        
        bot.send_document(uid, bio, caption="✅ <b>Extracted Numbers</b>")
        bot.send_message(uid, "✅ <b>Extraction Completed Successfully!</b> 🎉", reply_markup=main_menu())
        user_data[uid] = {'state': 'IDLE'}

print("Bot is running...")
bot.infinity_polling(skip_pending=True)`