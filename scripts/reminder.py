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
ACK_MESSAGE = os.getenv("ACK_MESSAGE", "收到，下个月初再提醒你")
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


def normalize_update_id(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def is_private_target_reply(message: dict) -> bool:
    user = message.get("from") or {}
    chat = message.get("chat") or {}
    text = message.get("text")

    if not text:
        return False
    if not TARGET_USER_ID or str(user.get("id")) != TARGET_USER_ID:
        return False

    # Only count direct private messages to this bot. Messages from groups or supergroups must not acknowledge the reminder.
    if chat.get("type") != "private":
        return False

    # In private chats, Telegram chat id normally equals user id. This extra check prevents accidental acknowledgement from another private chat.
    return str(chat.get("id")) == TARGET_USER_ID


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
        if is_private_target_reply(message):
            found_reply = True

    return found_reply


def send_message(text: str) -> None:
    telegram_api("sendMessage", {"chat_id": CHAT_ID, "text": text})


def send_reminder() -> None:
    try:
        send_message(REMINDER_MESSAGE)
    except TelegramApiError as error:
        error_text = str(error)
        if "chat not found" in error_text.lower() or "bot can't initiate conversation" in error_text.lower():
            raise RuntimeError("Telegram could not send the private message. Open Telegram and send /start or any message to this bot first, then rerun the workflow.") from error
        raise


def send_acknowledgement() -> None:
    try:
        send_message(ACK_MESSAGE)
    except TelegramApiError as error:
        print(f"Warning: failed to send acknowledgement message: {error}")


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
        send_acknowledgement()
        print("Target user replied in private chat. Reminder is paused until next month.")
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
