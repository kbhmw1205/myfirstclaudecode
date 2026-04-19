import json
import os
import re
from datetime import datetime, timedelta, timezone

import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

DATES_FILE = "dates.json"
STATE_FILE = "state.json"

KST = timezone(timedelta(hours=9))

HELP_TEXT = (
    "📖 사용법\n"
    "\n"
    "/복귀 MM-DD → 복귀일 등록 (예: /복귀 01-25)\n"
    "/목록 → 등록된 복귀일 보기\n"
    "/삭제 → 모든 복귀일 삭제\n"
    "/도움 → 이 도움말"
)

CHECKLIST = (
    "🔔 복귀 알림! 오늘 19:30 출발 전 확인!\n"
    "\n"
    "□ 교정 유지장치\n"
    "□ 휴가증\n"
    "□ 패스\n"
    "□ 카드\n"
    "\n"
    "다 챙겼으면 출발! 🫡"
)


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def send_message(text):
    resp = requests.post(
        f"{API_URL}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text},
    )
    resp.raise_for_status()


def parse_return_command(text):
    m = re.match(r"^/복귀\s+(\d{1,2})-(\d{1,2})\s*$", text.strip())
    if not m:
        return None
    month, day = int(m.group(1)), int(m.group(2))
    today = datetime.now(KST).date()
    try:
        target = datetime(today.year, month, day).date()
    except ValueError:
        return None
    if target < today:
        target = datetime(today.year + 1, month, day).date()
    return target.isoformat()


def process_message(text, dates):
    text = text.strip()
    if text.startswith("/복귀"):
        date_str = parse_return_command(text)
        if date_str is None:
            send_message("❌ 날짜 형식이 잘못됐어요.\n예: /복귀 01-25")
            return
        if date_str not in dates["dates"]:
            dates["dates"].append(date_str)
            dates["dates"].sort()
        d = datetime.fromisoformat(date_str)
        send_message(f"✅ {d.month}월 {d.day}일 19:30 알림 등록! 🫡")
    elif text.startswith("/목록"):
        if dates["dates"]:
            lines = "\n".join(f"• {d}" for d in dates["dates"])
            send_message(f"📅 등록된 복귀일:\n{lines}")
        else:
            send_message("등록된 복귀일이 없어요.")
    elif text.startswith("/삭제"):
        dates["dates"] = []
        send_message("🗑️ 모든 복귀일 삭제 완료.")
    elif text.startswith("/도움") or text.startswith("/start") or text.startswith("/help"):
        send_message(HELP_TEXT)


def poll_messages(dates):
    state = load_json(STATE_FILE, {"last_update_id": 0})

    params = {"timeout": 0}
    if state["last_update_id"]:
        params["offset"] = state["last_update_id"] + 1

    resp = requests.get(f"{API_URL}/getUpdates", params=params)
    resp.raise_for_status()
    updates = resp.json().get("result", [])

    for update in updates:
        state["last_update_id"] = update["update_id"]
        msg = update.get("message")
        if msg and msg.get("text"):
            process_message(msg["text"], dates)

    save_json(STATE_FILE, state)


def check_and_send_reminder(dates):
    now = datetime.now(KST)
    today = now.date().isoformat()

    # 19:25 ~ 20:59 KST 사이에만 알림 발송
    if now.hour < 19 or (now.hour == 19 and now.minute < 25):
        return
    if now.hour >= 21:
        return

    if today in dates["dates"]:
        send_message(CHECKLIST)
        dates["dates"].remove(today)


def main():
    dates = load_json(DATES_FILE, {"dates": []})
    poll_messages(dates)
    check_and_send_reminder(dates)
    save_json(DATES_FILE, dates)


if __name__ == "__main__":
    main()
