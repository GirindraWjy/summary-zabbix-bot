from auth.auth import get_sheet
from config import HOST_MAP, ZABBIX_AUTH, ZABBIX_URL, ITEMIDS_MEMORY_MAP, ITEMIDS_SUMMARY
import requests
import json
import math
import datetime
from telegram import Update
from decimal import Decimal
from telegram.ext import ContextTypes

from auth.auth import get_sheet

def insert_to_summary(values):
    sheet = get_sheet()

    start_row = 4
    start_col = 3 

    row_values = sheet.row_values(start_row)
    col_index = start_col
    while col_index <= len(row_values) and row_values[col_index-1] != "":
        col_index += 1

    for i, val in enumerate(values):
        sheet.update_cell(start_row + i, col_index, val)

    print(f"[LOG] Data {values} ditulis mulai dari kolom {col_index} ke bawah")

async def specific_summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("[LOG] Menjalankan service: specific_summary_command")
    if len(context.args) == 0:
        await update.message.reply_text(
            "Gunakan format:\n"
            "- /summary <HH:MM> (jam hari ini)\n"
            "- /summary <DD/MM/YYYY HH:MM> (tanggal + jam spesifik)"
        )
        return

    user_input = " ".join(context.args)  # gabungkan semua argumen
    try:
        # coba format lengkap DD/MM/YYYY HH:MM
        try:
            dt_wib = datetime.datetime.strptime(user_input, "%d/%m/%Y %H:%M")
            print(f"[LOG] Input user format tanggal: {dt_wib}")
        except ValueError:
            # fallback ke format jam saja HH:MM (pakai tanggal hari ini)
            jam, menit = map(int, user_input.split(":"))
            today = datetime.date.today()
            dt_wib = datetime.datetime(today.year, today.month, today.day, jam, menit, 0)
            print(f"[LOG] Input user format jam: {dt_wib}")

        time_from = int(dt_wib.timestamp())
        time_till = time_from + 100

    except Exception as e:
        await update.message.reply_text(
            "Format salah. Gunakan HH:MM atau DD/MM/YYYY HH:MM\n"
            "Contoh: 02:00 atau 10/05/2026 23:00"
        )
        print(f"[ERROR] Parsing gagal: {e}")
        return

    await update.message.reply_text("⏳ Sedang menambahkan data summary, mohon ditunggu...")

    print(f"[LOG] Epoch awal - akhir: {time_from} - {time_till}")

    all_itemids = list(ITEMIDS_SUMMARY)

    payload_hist = {
        "jsonrpc": "2.0",
        "method": "history.get",
        "params": {
            "output": "extend",
            "history": 0,
            "itemids": all_itemids,
            "time_from": time_from,
            "time_till": time_till,
            "sortfield": "clock",
            "sortorder": "DESC"
        },
        "auth": ZABBIX_AUTH,
        "id": 2
    }

    print("[LOG] Payload yang dikirim ke Zabbix:")
    print(json.dumps(payload_hist, indent=2))

    response_hist = requests.post(ZABBIX_URL, json=payload_hist).json()
    rows = response_hist.get("result", [])

    earliest = {}
    for row in rows:
        iid = row["itemid"]
        if iid not in earliest or int(row["clock"]) < int(earliest[iid]["clock"]):
            earliest[iid] = row

    results = []
    for iid in ITEMIDS_SUMMARY:
        if iid in earliest:
            value = float(earliest[iid]["value"])
            if value >= 10:
                formatted = str(int(value))  # integer
            elif value < 0.1:
                truncated = math.floor(value * 100) / 100
                formatted = f"{truncated:.2f}"  # 2 desimal
            else:
                truncated = math.floor(value * 10) / 10
                formatted = f"{truncated:.1f}"  # 1 desimal
            results.append(formatted)
        else:
            results.append(f"Item {iid}: data tidak ditemukan")

    print("[LOG] Hasil summary:")
    for line in results:
        print("   " + line)

    try:
        insert_to_summary(results)
        print("[LOG] Summary berhasil ditulis ke Google Sheets")
    except Exception as e:
        print(f"[ERROR] Gagal insert ke Summary: {e}")

    await update.message.reply_text("✅ Summary berhasil ditambahkan, silahkan dicek di Google Sheets")
    
def wib_to_epoch(hour: int, minute: int) -> int:
    today = datetime.date.today()
    dt_wib = datetime.datetime(today.year, today.month, today.day, hour, minute, 0)
    return int(dt_wib.timestamp())
