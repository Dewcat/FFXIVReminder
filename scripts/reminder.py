import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

STATE_PATH = Path("state/reminder_state.json")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TARGET_USER_ID = os.getenv("TELEGRAM_TARGET_USER_ID", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip() or TARGET_USER_ID
REMINDER_MESSAGE = os.getenv("REMINDER_MESSAGE", "记得上号保部队房")
TIMEZONE = os.getenv("REMINDER_TIMEZONE", "Asia/Shanghai")

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


class TelegramApiError(RuntimeError):
    pass


def telegram_api(method: str, params: dict | None = None) -> dict:
    params = params or {}
    data = urllib.parse.urlencode(params).encode("utf-8")
    request = urllib.request.Request(f"{API_BASE}/{method}", data=data, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise TelegramApiError(f"Telegram API {method} HTTP {error.code}: {body}") from error

    if not payload.get("ok"):
        raise TelegramApiError(f"Telegram API {method} failed: {payload}")
    return payload


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def current_month() -> str:
    return datetime.now(ZoneInfo(TIMEZONE)).strftime("%Y-%m")


def is_target_user(user: dict) -> bool:
    return bool(TARGET_USER_ID) and str(user.get("id")) == TARGET_USER_ID


def normalize_update_id(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def consume_target_replies(state: dict) -> bool:
    if not TARGET_USER_ID:
        print("Warning: TELEGRAM_TARGET_USER_ID is not set, so reply detection is disabled for this run.")
        return False

    params = {
        "timeout": 0,
        "allowed_updates": json.dumps(["message"]),
    }
    last_update_id = normalize_update_id(state.get("last_update_id"))
    if last_update_id is not None:
        params["offset"] = last_update_id + 1

    try:
        payload = telegram_api("getUpdates", params)
    except TelegramApiError as error:
        error_text = str(error)
        if "Conflict" in error_text or "terminated by other getUpdates request" in error_text:
            print("Warning: getUpdates is currently occupied by another bot process. Reminder sending will continue, but reply detection will be skipped in this run.")
            return False
        raise

    updates = payload.get("result", [])
    found_reply = False
    for update in updates:
        update_id = normalize_update_id(update.get("update_id"))
        if update_id is not None:
            previous_update_id = normalize_update_id(state.get("last_update_id"))
            state["last_update_id"] = max(previous_update_id or update_id, update_id)

        message = update.get("message") or {}
        user = message.get("from") or {}
        text = message.get("text")
        if text and is_target_user(user):
            found_reply = True

    return found_reply


def send_reminder() -> None:
    try:
        telegram_api("sendMessage", {"chat_id": CHAT_ID, "text": REMINDER_MESSAGE})
    except TelegramApiError as error:
        error_text = str(error)
        if "chat not found" in error_text.lower() or "bot can't initiate conversation" in error_text.lower():
            raise RuntimeError("Telegram could not send the private message. Open Telegram and send /start or any message to this bot first, then rerun the workflow.") from error
        raise


def main() -> int:
    if not BOT_TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN. Add it in Settings -> Secrets and variables -> Actions -> Secrets.")
    if not CHAT_ID:
        raise RuntimeError("Missing chat destination. Set TELEGRAM_CHAT_ID or TELEGRAM_TARGET_USER_ID in Settings -> Secrets and variables -> Actions -> Secrets.")

    state = load_state()
    month_key = current_month()

    if state.get("month") != month_key:
        state = {
            "month": month_key,
            "acknowledged": False,
            "last_update_id": normalize_update_id(state.get("last_update_id")),
        }

    if consume_target_replies(state):
        state["acknowledged"] = True
        save_state(state)
        print("Target user replied. Reminder is paused until next month.")
        return 0

    if state.get("acknowledged"):
        save_state(state)
        print("Already acknowledged this month. No reminder sent.")
        return 0

    send_reminder()
    state["last_sent_at"] = datetime.now(ZoneInfo(TIMEZONE)).isoformat()
    save_state(state)
    print("Reminder sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
