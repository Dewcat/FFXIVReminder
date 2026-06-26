# FFXIVReminder

GitHub Actions version of the Telegram reminder.

## What it does

At 20:00 Asia/Shanghai every day, the workflow checks whether the target Telegram user has replied this month.

- On the first run of each month, it sends: `记得上号保部队房`
- If the target user has not replied, it sends the same message again every day at 20:00.
- Once the target user replies with any text message, it stops sending reminders until the next month.
- At the next month, the reminder cycle resets automatically.

## Required GitHub Secrets

Open the repository settings:

`Settings` -> `Secrets and variables` -> `Actions` -> `Secrets`

Add these secrets:

| Secret | Meaning |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token from BotFather. |
| `TELEGRAM_TARGET_USER_ID` | Your numeric Telegram user id. This is used to detect your replies and can also be used as the private-chat destination. |

Optional secret:

| Secret | Meaning |
| --- | --- |
| `TELEGRAM_CHAT_ID` | The chat id to send reminders to. For a private chat, this can usually be omitted if `TELEGRAM_TARGET_USER_ID` is set and you have already messaged the bot. |

## Optional GitHub Variables

Open:

`Settings` -> `Secrets and variables` -> `Actions` -> `Variables`

You can add:

| Variable | Default |
| --- | --- |
| `TELEGRAM_TARGET_USERNAME` | Empty. Only needed if you prefer username matching instead of user-id matching. |
| `REMINDER_MESSAGE` | `记得上号保部队房` |
| `REMINDER_TIMEZONE` | `Asia/Shanghai` |

## Getting chat id and user id

1. Send any message to your Telegram bot.
2. Open this URL in a browser, replacing `<TOKEN>` with your bot token:

```text
https://api.telegram.org/bot<TOKEN>/getUpdates
```

3. In the returned JSON:
   - `message.chat.id` is `TELEGRAM_CHAT_ID`
   - `message.from.id` is `TELEGRAM_TARGET_USER_ID`

## Important note

This workflow uses Telegram `getUpdates`, so the bot must not have an active webhook. If you previously set a webhook, clear it once:

```text
https://api.telegram.org/bot<TOKEN>/deleteWebhook
```

## Manual test

Go to `Actions` -> `FFXIV Telegram Reminder` -> `Run workflow`.
