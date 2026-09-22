from auth.auth import get_sheet
from config import HOST_MAP, ZABBIX_AUTH, ZABBIX_URL, ITEMIDS_MEMORY_MAP, ITEMIDS_SUMMARY
import requests
import json
import math
import datetime
from telegram import Update
from decimal import Decimal
from telegram.ext import ContextTypes


def column_letter(column_number: int) -> str:
    result = ""

    while column_number > 0:
        column_number, remainder = divmod(column_number - 1, 26)
        result = chr(65 + remainder) + result

    return result


def insert_to_summary(values):
    sheet = get_sheet()
    sheet_summary = sheet["Summary"]

    start_row = 4
    start_col = 3

    row_values = sheet_summary.row_values(start_row)

    col_index = start_col
    while col_index <= len(row_values) and row_values[col_index - 1] != "":
        col_index += 1

    col_letter = column_letter(col_index)

    start_cell = f"{col_letter}{start_row}"
    end_cell = f"{col_letter}{start_row + len(values) - 1}"
    range_name = f"{start_cell}:{end_cell}"

    data = [[value] for value in values]

    sheet_summary.update(
        range_name,
        data
    )

    print(
        f"[LOG] {len(values)} data berhasil ditulis  "
        f"ke Summary!{range_name}"
    )


async def specific_summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("[LOG] Menjalankan service: specific_summary_command")

    if len(context.args) == 0:
        await update.message.reply_text(
            "Gunakan format:\n"
            "- /summary <HH:MM> (jam hari ini)\n"
            "- /summary <DD/MM/YYYY HH:MM> (tanggal + jam spesifik)"
        )
        return

    user_input = " ".join(context.args)

    try:
        try:
            dt_wib = datetime.datetime.strptime(
                user_input,
                "%d/%m/%Y %H:%M"
            )
            print(f"[LOG] Input user format tanggal: {dt_wib}")

        except ValueError:
            jam, menit = map(int, user_input.split(":"))
            today = datetime.date.today()

            dt_wib = datetime.datetime(
                today.year,
                today.month,
                today.day,
                jam,
                menit,
                0
            )

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

    await update.message.reply_text(
        "⏳ Sedang menambahkan data summary, mohon ditunggu..."
    )

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

    try:
        response = requests.post(
            ZABBIX_URL,
            json=payload_hist,
            timeout=30
        )

        response.raise_for_status()
        response_hist = response.json()

    except requests.RequestException as e:
        print(f"[ERROR] Request ke Zabbix gagal: {e}")

        await update.message.reply_text(
            "❌ Gagal mengambil data dari Zabbix."
        )
        return

    except ValueError as e:
        print(f"[ERROR] Response Zabbix bukan JSON valid: {e}")

        await update.message.reply_text(
            "❌ Response dari Zabbix tidak valid."
        )
        return

    if "error" in response_hist:
        print("[ERROR] Zabbix API Error:")
        print(json.dumps(response_hist["error"], indent=2))

        await update.message.reply_text(
            "❌ Zabbix API mengembalikan error."
        )
        return

    rows = response_hist.get("result", [])

    earliest = {}

    for row in rows:
        iid = row["itemid"]

        if iid not in earliest or int(row["clock"]) < int(earliest[iid]["clock"]):
            earliest[iid] = row

    results = []

    for iid in ITEMIDS_SUMMARY:
        if iid in earliest:
            try:
                value = float(earliest[iid]["value"])

                if value >= 10:
                    formatted = str(int(value))

                elif value < 0.1:
                    truncated = math.floor(value * 100) / 100
                    formatted = f"{truncated:.2f}"

                else:
                    truncated = math.floor(value * 10) / 10
                    formatted = f"{truncated:.1f}"

                results.append(formatted)

            except (ValueError, TypeError) as e:
                print(f"[ERROR] Gagal format item {iid}: {e}")
                results.append(f"Item {iid}: value tidak valid")

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

        await update.message.reply_text(
            "❌ Data Zabbix berhasil diambil, tetapi gagal "
            "menulis ke Google Sheets."
        )
        return

    await update.message.reply_text(
        "✅ Summary berhasil ditambahkan, silahkan dicek di Google Sheets"
    )


def wib_to_epoch(hour: int, minute: int) -> int:
    today = datetime.date.today()

    dt_wib = datetime.datetime(
        today.year,
        today.month,
        today.day,
        hour,
        minute,
        0
    )

    return int(dt_wib.timestamp())