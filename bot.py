import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from service.memory import per_mem, realtime_memory_command, specific_memory_command
from service.alarm import check_cpu
from service.cpu import per_cpu, realtime_cpu_command, specific_cpu_command
from service.disk import per_disk, realtime_disk_command, specific_disk_command
from service.summary import insert_to_summary, specific_summary_command
from service.main.start import start, stop
from service.main.help import help
from config import TOKEN

async def allmem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await realtime_memory_command(update, context)
    else:
        await specific_memory_command(update, context)
        
async def allcpu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await realtime_cpu_command(update, context)
    else:
        await specific_cpu_command(update, context)
        
async def alldisk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await realtime_disk_command(update, context)
    else:
        await specific_disk_command(update, context)
        
async def insert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    test_values = ["Test1", "Test2", "Test3"]
    insert_to_summary(test_values)
    await update.message.reply_text(f"[LOG] Data {test_values} berhasil ditulis ke Summary")

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = update.message.text
    await update.message.reply_text(f"⚠️ Command {cmd} tidak ada. Silakan cek /help untuk daftar command yang tersedia.")
    
def main():
    
    app = Application.builder().token(TOKEN).build()
    restore_jobs(app)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("mem", per_mem))
    app.add_handler(CommandHandler("cpu", per_cpu))
    app.add_handler(CommandHandler("disk", per_disk))
    app.add_handler(CommandHandler("allmem", allmem_command))
    app.add_handler(CommandHandler("allcpu", allcpu_command))
    app.add_handler(CommandHandler("alldisk", alldisk_command))
    app.add_handler(CommandHandler("insert", insert_command))
    app.add_handler(CommandHandler("summary", specific_summary_command))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    print("Bot berjalan...")
    
    
    # try:
    #     with open("chat_ids.txt") as f:
    #         chat_ids = [line.strip() for line in f if line.strip()]
    #         print("[LOG] Chat ID tersimpan:")
    #         for cid in chat_ids:
    #             print(f" - {cid}")
    #             app.job_queue.run_repeating(check_cpu, interval=20, first=0, chat_id=int(cid))
    # except FileNotFoundError:
    #     print("[LOG] Belum ada chat_id tersimpan, jalankan /start dulu.")
        
    app.run_polling()
    
def restore_jobs(application):
    try:
        with open("chat_ids.txt") as f:
            chat_ids = [line.strip() for line in f if line.strip()]
        for cid in chat_ids:
            application.job_queue.run_repeating(
                check_cpu,
                interval=20,
                first=0,
                chat_id=int(cid),
                name=cid
            )
        print(f"[LOG] Jobs dipulihkan untuk Chat IDs: {chat_ids}")
    except FileNotFoundError:
        print("[LOG] Tidak ada chat_ids.txt, tidak ada job dipulihkan")


if __name__ == "__main__":
    main()