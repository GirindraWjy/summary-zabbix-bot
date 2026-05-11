import datetime
from telegram import Update
from telegram.ext import ContextTypes
from service.alarm import check_cpu

user_chat_ids = set()

def save_chat_id(chat_id: int):
    try:
        with open("chat_ids.txt") as f:
            existing = {line.strip() for line in f}
    except FileNotFoundError:
        existing = set()

    if str(chat_id) not in existing:
        with open("chat_ids.txt", "a") as f:
            f.write(str(chat_id) + "\n")
        print(f"[LOG] Chat ID {chat_id} baru tersimpan ke chat_ids.txt")
    else:
        print(f"[LOG] Chat ID {chat_id} sudah ada, tidak disimpan ulang.")

def remove_chat_id(chat_id: int):
    try:
        with open("chat_ids.txt") as f:
            lines = [line.strip() for line in f if line.strip()]
        new_lines = [line for line in lines if line != str(chat_id)]
        with open("chat_ids.txt", "w") as f:
            f.write("\n".join(new_lines) + ("\n" if new_lines else ""))
        print(f"[LOG] Chat ID {chat_id} dihapus dari chat_ids.txt")
    except FileNotFoundError:
        print("[LOG] File chat_ids.txt belum ada, tidak ada yang dihapus.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    print("Chat ID:", chat_id)

    user_chat_ids.add(chat_id)
    save_chat_id(chat_id)

    context.job_queue.run_repeating(
    check_cpu,
    interval=20,
    first=0,
    chat_id=chat_id,
    name=str(chat_id)
    )


    await update.message.reply_text(
    "📌 Command:\n"
    "- /help → informasi command\n"
    "- /mem _server_ → cek memory per server\n"
    "- /cpu _server_ → cek CPU server tertentu\n"
    "- /disk _server_ → cek Disk server tertentu\n"
    "- /allmem → summary memory\n"
    "- /allmem HH:MM → summary memory spesifik\n"
    "- /allcpu → summary CPU\n"
    "- /allcpu HH:MM → summary CPU spesifik\n"
    "- /alldisk → summary Disk\n"
    "- /alldisk HH:MM → summary Disk spesifik\n"
    "- /summary HH:MM _atau_ DD/MM/YYYY HH:MM → insert summary di jam atau hari tertentu\n"
    "- /stop → hentikan notifikasi CPU untuk chat ini\n",
    parse_mode="Markdown"
)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    remove_chat_id(chat_id)
    if chat_id in user_chat_ids:
        user_chat_ids.remove(chat_id)

    jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    if not jobs:
        print(f"[LOG] Tidak ada job ditemukan untuk Chat ID {chat_id}")
    for job in jobs:
        job.remove()  # langsung hapus
        print(f"[LOG] Job {job.name} untuk Chat ID {chat_id} dihapus dari job queue.")
        
    active_jobs = [job.name for job in context.job_queue.jobs()]
    print(f"[DEBUG] Jobs aktif setelah stop: {active_jobs}")

    await update.message.reply_text("🚫 Alert CPU dihentikan untuk chat ini.")