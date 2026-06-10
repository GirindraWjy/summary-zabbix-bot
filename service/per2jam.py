from telegram import Update
from telegram.ext import ContextTypes
from auth.auth import get_sheet
from config import ZABBIX_AUTH, ZABBIX_URL, ITEMIDS_SUMMARY
import datetime
import requests
import math

BLOCK_HEIGHT = 20
EMPTY_GAP = 1

LAST_TEMPLATE_ROW = None

# =========================================
# TEMPLATE
# =========================================

def get_next_row(sheet):

    values = sheet.get_all_values()

    last_used_row = 0

    for idx, row in enumerate(values, start=1):

        if any(str(cell).strip() for cell in row):
            last_used_row = idx

    return last_used_row + EMPTY_GAP + 1


def cell_request(sheet_id, row, col, value):

    return {
        "updateCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": row,
                "endRowIndex": row + 1,
                "startColumnIndex": col,
                "endColumnIndex": col + 1
            },

            "rows": [{
                "values": [{
                    "userEnteredValue": {
                        "stringValue": str(value)
                    }
                }]
            }],

            "fields": "userEnteredValue"
        }
    }


def insert_twohour_template(
    nama,
    tanggal,
    waktu,
    shift
):

    global LAST_TEMPLATE_ROW

    sheet = get_sheet()["Per 2 Jam"]

    spreadsheet = sheet.spreadsheet

    target_row = get_next_row(sheet)

    LAST_TEMPLATE_ROW = target_row

    base = target_row - 1

    requests = [

        {
            "copyPaste": {

                "source": {
                    "sheetId": sheet.id,
                    "startRowIndex": 0,
                    "endRowIndex": 20,
                    "startColumnIndex": 0,
                    "endColumnIndex": 22
                },

                "destination": {
                    "sheetId": sheet.id,
                    "startRowIndex": base,
                    "endRowIndex": base + BLOCK_HEIGHT,
                    "startColumnIndex": 0,
                    "endColumnIndex": 22
                },

                "pasteType": "PASTE_NORMAL",
                "pasteOrientation": "NORMAL"
            }
        },

        # NAMA
        cell_request(
            sheet.id,
            base + 1,
            0,
            f"SUMMARY JAGA INAP\n{nama}"
        ),

        # TANGGAL
        cell_request(
            sheet.id,
            base + 4,
            0,
            tanggal
        ),

        # SHIFT
        cell_request(
            sheet.id,
            base + 4,
            1,
            shift
        ),

        # WAKTU
        cell_request(
            sheet.id,
            base + 4,
            2,
            waktu
        )
    ]

    spreadsheet.batch_update({
        "requests": requests
    })


def insert_status_result(results):

    global LAST_TEMPLATE_ROW

    sheet = get_sheet()["Per 2 Jam"]

    # ROW STATUS (row OK/NOK)
    status_row = LAST_TEMPLATE_ROW + 7

    requests = []

    # =========================================
    # GROUP ITEMID
    # =========================================

    server_groups = [

        ("36", 0, 3),
        ("37", 3, 6),
        ("41", 6, 9),
        ("42", 9, 12),
        ("43", 12, 15),
        ("44", 15, 18),
        ("45", 18, 21),
        ("46", 21, 24),
        ("47", 24, 27),
        ("48", 27, 30),

        ("Zabbix", 30, 33),

        ("35", 33, 35),
        ("61", 35, 37),
        ("57", 37, 39),
        ("58", 39, 41),
        ("59", 41, 43),
    ]

    # =========================================
    # KOLOM SHEET
    # =========================================
    # F sampai U
    # F=5, G=6, dst

    column_map = [

        5,   # Server 36
        6,   # Server 37
        7,   # Server 41
        8,   # Server 42
        9,   # Server 43
        10,  # Server 44
        11,  # Server 45
        12,  # Server 46
        13,  # Server 47
        14,  # Server 48

        15,  # Zabbix

        16,  # Server 35
        17,  # Server 61
        18,  # Server 57
        19,  # Server 58
        20   # Server 59
    ]

    # =========================================
    # LOOP
    # =========================================

    for idx, (_, start, end) in enumerate(server_groups):

        values = []

        for val in results[start:end]:

            try:

                clean = str(val).replace("%", "").strip()

                values.append(float(clean))

            except:
                pass

        is_nok = any(v > 75 for v in values)

        status_text = "NOK" if is_nok else "OK"

        bg = (
            {"red": 1, "green": 0, "blue": 0}
            if is_nok
            else {"red": 0, "green": 1, "blue": 0}
        )

        col = column_map[idx]

        # =========================================
        # SERVER 35-59
        # MERGED ROW 9-10
        # =========================================

        if idx >= 11:

            start_row = LAST_TEMPLATE_ROW + 7
            end_row = LAST_TEMPLATE_ROW + 9

        # =========================================
        # SERVER NORMAL
        # STATUS DI ROW 10
        # =========================================

        else:

            start_row = LAST_TEMPLATE_ROW + 8
            end_row = LAST_TEMPLATE_ROW + 9

        requests.append({

            "repeatCell": {

                "range": {

                    "sheetId": sheet.id,

                    "startRowIndex": start_row,
                    "endRowIndex": end_row,

                    "startColumnIndex": col,
                    "endColumnIndex": col + 1
                },

                "cell": {

                    "userEnteredValue": {
                        "stringValue": status_text
                    },

                    "userEnteredFormat": {

                        "backgroundColor": bg,

                        "horizontalAlignment": "CENTER",

                        "textFormat": {
                            "bold": True
                        }
                    }
                },

                "fields":
                    "userEnteredValue,"
                    "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        })

    sheet.spreadsheet.batch_update({
        "requests": requests
    })

    print("[LOG] Status OK/NOK berhasil dimasukkan")
# =========================================
# INSERT SUMMARY RESULT
# =========================================

def insert_summary_result(results):

    global LAST_TEMPLATE_ROW

    if LAST_TEMPLATE_ROW is None:

        print("[ERROR] LAST_TEMPLATE_ROW kosong")

        return

    sheet = get_sheet()["Per 2 Jam"]

    start_row = LAST_TEMPLATE_ROW + 5

    positions = [

        # SERVER 36
        (0, 0), (1, 0), (2, 0),

        # SERVER 37
        (0, 1), (1, 1), (2, 1),

        # SERVER 41
        (0, 2), (1, 2), (2, 2),

        # SERVER 42
        (0, 3), (1, 3), (2, 3),

        # SERVER 43
        (0, 4), (1, 4), (2, 4),

        # SERVER 44
        (0, 5), (1, 5), (2, 5),

        # SERVER 45
        (0, 6), (1, 6), (2, 6),

        # SERVER 46
        (0, 7), (1, 7), (2, 7),

        # SERVER 47
        (0, 8), (1, 8), (2, 8),

        # SERVER 48
        (0, 9), (1, 9), (2, 9),

        # ZABBIX
        (0,10), (1,10), (2,10),

        # SERVER 35
        (0,11), (1,11),

        # SERVER 61
        (0,12), (1,12),

        # SERVER 57
        (0,13), (1,13),

        # SERVER 58
        (0,14), (1,14),

        # SERVER 59
        (0,15), (1,15),
    ]

    requests = []

    for index, value in enumerate(results):

        row_offset, col_offset = positions[index]

        requests.append({

            "updateCells": {

                "range": {

                    "sheetId": sheet.id,

                    "startRowIndex": start_row + row_offset,
                    "endRowIndex": start_row + row_offset + 1,

                    # MULAI KOLOM F
                    "startColumnIndex": 5 + col_offset,
                    "endColumnIndex": 6 + col_offset
                },

                "rows": [{
                    "values": [{
                        "userEnteredValue": {
                            "stringValue": str(value)
                        }
                    }]
                }],

                "fields": "userEnteredValue"
            }
        })

    sheet.spreadsheet.batch_update({
        "requests": requests
    })

    print("[LOG] Summary berhasil dimasukkan")


# =========================================
# COMMAND
# =========================================

async def twohour_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    print("[LOG] Menjalankan service: twohour_command")

    try:

        args = context.args

        if len(args) < 4:

            await update.message.reply_text(
                "❌ Format salah\n\n"
                "Contoh:\n"
                "/2jam Girindra 10/06/2026 15:00 2"
            )

            return

        nama, tanggal, waktu, shift = args[:4]

        await update.message.reply_text(
            "⏳ Tunggu Sebentar..."
        )

        # =====================================
        # BUAT TEMPLATE
        # =====================================

        insert_twohour_template(
            nama,
            tanggal,
            waktu,
            shift
        )

        # =====================================
        # HIT ZABBIX
        # =====================================

        dt_wib = datetime.datetime.strptime(
            f"{tanggal} {waktu}",
            "%d/%m/%Y %H:%M"
        )

        time_from = int(dt_wib.timestamp())

        time_till = time_from + 100

        payload_hist = {
            "jsonrpc": "2.0",
            "method": "history.get",
            "params": {
                "output": "extend",
                "history": 0,
                "itemids": ITEMIDS_SUMMARY,
                "time_from": time_from,
                "time_till": time_till,
                "sortfield": "clock",
                "sortorder": "DESC"
            },
            "auth": ZABBIX_AUTH,
            "id": 2
        }

        response_hist = requests.post(
            ZABBIX_URL,
            json=payload_hist
        ).json()

        rows = response_hist.get("result", [])

        print(f"[LOG] Total data Zabbix: {len(rows)}")

        earliest = {}

        for row in rows:

            iid = row["itemid"]

            if (
                iid not in earliest
                or int(row["clock"]) < int(earliest[iid]["clock"])
            ):

                earliest[iid] = row

        results = []

        for iid in ITEMIDS_SUMMARY:

            if iid in earliest:

                value = float(
                    earliest[iid]["value"]
                )

                if value >= 10:

                    formatted = str(int(value))

                elif value < 0.1:

                    truncated = (
                        math.floor(value * 100) / 100
                    )

                    formatted = f"{truncated:.2f}"

                else:

                    truncated = (
                        math.floor(value * 10) / 10
                    )

                    formatted = f"{truncated:.1f}"

                results.append(formatted)

            else:

                results.append("-")

        print("[LOG] Hasil Summary:")

        for line in results:
            print("   " + line)

        # =====================================
        # INSERT KE SHEET
        # =====================================

        insert_summary_result(results)
        insert_status_result(results)

        print(
            f"[LOG] Template berhasil dibuat | "
            f"Nama: {nama} | "
            f"Tanggal: {tanggal} | "
            f"Waktu: {waktu} | "
            f"Shift: {shift} | "
            f"Row: {LAST_TEMPLATE_ROW}"
        )

        await update.message.reply_text(
            "✅ Per 2 Jam berhasil dibuat."
        )

    except Exception as e:

        print(f"[ERROR] {e}")

        await update.message.reply_text(
            f"❌ Gagal:\n{e}"
        )