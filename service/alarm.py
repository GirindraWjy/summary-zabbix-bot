import time
import requests
from telegram.ext import ContextTypes
from config import HOST_MAP, ZABBIX_AUTH, ZABBIX_URL
last_alert_time = {}

THRESHOLD = 70
ALERT_INTERVAL = 300
HOST_REVERSE_MAP = {v: k for k, v in HOST_MAP.items()}

async def check_cpu(context: ContextTypes.DEFAULT_TYPE):
    job_name = getattr(context.job, "name", None)
    chat_id = getattr(context.job, "chat_id", None)
    print(f"[LOG] Menjalankan service: check_cpu (job={job_name}, chat_id={chat_id})")

    now = time.time()

    hostids = list(HOST_MAP.values())

    payload = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "params": {
            "output": ["itemid", "name", "value_type", "lastvalue", "hostid"],
            "hostids": hostids,
            "search": {"name": "CPU Utilization"}
        },
        "auth": ZABBIX_AUTH,
        "id": 2
    }

    try:
        response = requests.post(ZABBIX_URL, json=payload)
        data = response.json()

        if "result" in data and len(data["result"]) > 0:
            for item in data["result"]:
                hostid = item["hostid"]
                kode = HOST_REVERSE_MAP.get(hostid)
                if not kode:
                    continue

                lastvalue = float(item["lastvalue"])
                print(f"[LOG] VM {kode} CPU usage: {lastvalue:.2f}%")

                if lastvalue > THRESHOLD:
                    last_time = last_alert_time.get(kode, 0)
                    if now - last_time >= ALERT_INTERVAL:
                        await context.bot.send_message(
                            chat_id=context.job.chat_id,
                            text=f"‼️CPU VM {kode} has reached the Critical category, now CPU Usage is {lastvalue:.2f}%"
                        )
                        last_alert_time[kode] = now

    except Exception as e:
        await context.bot.send_message(chat_id=context.job.chat_id, text=f"Terjadi error: {e}")

