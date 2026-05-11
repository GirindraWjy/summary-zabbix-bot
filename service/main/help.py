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
    "- /allmem _jam_ → summary memory spesifik\n"
    "- /allcpu → summary CPU\n"
    "- /allcpu _jam_ → summary CPU spesifik\n"
    "- /alldisk → summary Disk\n"
    "- /alldisk _jam_ → summary Disk spesifik\n"
    "- /summary _jam_ → insert summary di jam tertentu\n"
    "- /stop → hentikan notifikasi CPU untuk chat ini\n",
    parse_mode="Markdown"
    )
