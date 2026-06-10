import datetime
from telegram import Update
from telegram.ext import  ContextTypes

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):

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
    "- /2jam name DD/MM/YYYY HH:MM Shift → absen per 2 jam\n"
    "- /summary HH:MM _atau_ DD/MM/YYYY HH:MM → insert summary di jam atau hari tertentu\n"
    "- /stop → hentikan notifikasi CPU untuk chat ini\n",
    parse_mode="Markdown"
    )
