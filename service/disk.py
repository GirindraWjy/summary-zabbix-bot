import requests
import datetime
from telegram import Update
from telegram.ext import ContextTypes
from config import DISK_HOST_MAP, ZABBIX_AUTH, ZABBIX_URL, ITEMIDS_DISK_MAP

async def per_disk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("[LOG] Menjalankan service: per_disk")
    if len(context.args) == 0:
        await update.message.reply_text("Gunakan format: /disk <VM>")
        return

    kode = context.args[0]
    hostid = DISK_HOST_MAP.get(kode)

    if not hostid:
        await update.message.reply_text(f"Disk Utilization VM {kode} tidak ditemukan.")
        return

    payload = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "params": {
            "output": ["itemid", "name", "value_type", "lastvalue", "hostid"],
            "hostids": hostid,
            "search": {"name": "Space utilization"}
        },
        "auth": ZABBIX_AUTH,
        "id": 2
    }

    try:
        response = requests.post(ZABBIX_URL, json=payload)
        data = response.json()

        if "result" in data and len(data["result"]) > 0:
            target_item = next(
                (item for item in data["result"]
                 if item["name"] in ["/data: Space utilization", "/data-first: Space utilization"]),
                None
            )

            if target_item:
                lastvalue = target_item["lastvalue"]
                value = f"{float(lastvalue):.2f}"
                await update.message.reply_text(
                    f"Disk Utilization VM {kode}: {value}%"
                )
            else:
                await update.message.reply_text("Tidak ada item /data atau /data-first ditemukan.")
        else:
            await update.message.reply_text("Data tidak ditemukan untuk VM tersebut.")
    except Exception as e:
        await update.message.reply_text(f"Terjadi error: {e}")
        
async def realtime_disk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("[LOG] Menjalankan service: realtime_disk_command")
    await update.message.reply_text("⏳ Disk Utilization Summary sedang diproses, mohon ditunggu...")

    hostids = list(DISK_HOST_MAP.values())

    payload = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "params": {
            "output": ["itemid", "name", "value_type", "lastvalue"],
            "hostids": hostids,
            "search": {"name": "Space Utilization"}
        },
        "auth": ZABBIX_AUTH,
        "id": 2
    }

    import json
    print("[LOG] Payload summary:")
    print(json.dumps(payload, indent=2))

    try:
        response = requests.post(ZABBIX_URL, json=payload)
        data = response.json()
        results = []

        if "result" in data and len(data["result"]) > 0:
            api_results = {row["itemid"]: row["lastvalue"] for row in data["result"]}

            # loop sesuai urutan ITEMIDS_CPU_MAP
            for kode in ITEMIDS_DISK_MAP.keys():
                iid = ITEMIDS_DISK_MAP[kode]
                if iid in api_results:
                    value = f"{float(api_results[iid]):.2f}"
                    results.append(f"VM {kode}: {value}%")
                else:
                    results.append(f"VM {kode}: data tidak ditemukan")
        else:
            results.append("Data tidak ditemukan")

    except Exception as e:
        results = [f"Error: {e}"]

    summary_text = "📊 CPU Utilization Summary:\n" + "\n".join(results)
    await update.message.reply_text(summary_text)

    print("[LOG] Hasil summary:")
    for line in results:
        print("   " + line)
        
        
async def specific_disk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("[LOG] Menjalankan service: specific_disk_command")
    if len(context.args) == 0:
        await update.message.reply_text("Gunakan format: /summary <HH:MM>")
        return

    try:
        jam, menit = map(int, context.args[0].split(":"))
    except ValueError:
        await update.message.reply_text("Format waktu salah. Gunakan HH:MM, contoh 02:00")
        return

    await update.message.reply_text("⏳ Disk Utilization Summary sedang diproses, mohon ditunggu...")

    time_from = wib_to_epoch(jam, menit)
    time_till = time_from + 100

    print(f"[LOG] Input user: {jam:02d}:{menit:02d} WIB, epoch awal - akhir: {time_from} - {time_till}")

    all_itemids = list(ITEMIDS_DISK_MAP.values())

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

    response_hist = requests.post(ZABBIX_URL, json=payload_hist).json()
    rows = response_hist.get("result", [])

    latest = {}
    for row in rows:
        iid = row["itemid"]
        if iid not in latest or int(row["clock"]) > int(latest[iid]["clock"]):
            latest[iid] = row

    results = []
    for kode, iid in ITEMIDS_DISK_MAP.items():
        if iid in latest:
            value = float(latest[iid]["value"])
            results.append(f"VM {kode}: {value:.2f}%")
        else:
            results.append(f"VM {kode}: data tidak ditemukan")

    summary_text = f"📊 Disk Utilization Summary {jam:02d}:{menit:02d} WIB:\n" + "\n".join(results)
    await update.message.reply_text(summary_text)

    print("[LOG] Hasil summary:")
    for line in results:
        print("   " + line)    
        
def wib_to_epoch(hour: int, minute: int) -> int:
    today = datetime.date.today()
    dt_wib = datetime.datetime(today.year, today.month, today.day, hour, minute, 0)
    # langsung ambil timestamp dari dt_wib tanpa dikurangi 7 jam
    return int(dt_wib.timestamp())
