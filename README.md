# FFXIVReminder

基于 GitHub Actions 的 FFXIV 部队房保房 Telegram 计时提醒器。

## 功能说明

每天 **Asia/Shanghai 时区 20:17**，工作流会运行一次，检查你距离上次上号确认已经过去多少天。

- 私聊回复 bot 任意文字消息，表示你当天已经上号保房。
- bot 读取到你的私聊回复后，会把计时重置为第 1 天，并发送：`收到，计时已重置为 1 天。`
- 群聊或超群里的消息不会被当作确认回复。
- 没有读取到回复的日子里，计时会按日期自动增加。
- 默认到第 30 天开始发送提醒：`记得上号保部队房，你已经 X 天没进了。`
- 达到提醒阈值后，每天最多提醒一次，直到你再次私聊回复 bot 重置计时。

## 必需的 GitHub Secrets

打开仓库设置：

`Settings` -> `Secrets and variables` -> `Actions` -> `Secrets`

添加以下 secrets：

| Secret | 含义 |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | 你从 BotFather 获取的 Telegram bot token。 |
| `TELEGRAM_TARGET_USER_ID` | 你的 Telegram 数字用户 ID。用于检测你的私聊回复，也可以作为私聊发送目标。 |

可选 secret：

| Secret | 含义 |
| --- | --- |
| `TELEGRAM_CHAT_ID` | 用于发送提醒的 chat id。对于私聊，如果已经设置了 `TELEGRAM_TARGET_USER_ID`，并且你已经给 bot 发过消息，通常可以不填。 |

## 可选的 GitHub Variables

打开：

`Settings` -> `Secrets and variables` -> `Actions` -> `Variables`

可以添加：

| Variable | 默认值 |
| --- | --- |
| `REMINDER_MESSAGE` | `记得上号保部队房，你已经 {days} 天没进了。` |
| `ACK_MESSAGE` | `收到，计时已重置为 1 天。` |
| `REMINDER_THRESHOLD_DAYS` | `30` |
| `REMINDER_TIMEZONE` | `Asia/Shanghai` |

`REMINDER_MESSAGE` 可以使用 `{days}`，运行时会被替换成当前计时天数。

## 获取 chat id 和 user id

1. 给你的 Telegram bot 发送任意消息。
2. 在浏览器中打开下面这个 URL，把 `<TOKEN>` 替换成你的 bot token：

```text
https://api.telegram.org/bot<TOKEN>/getUpdates
```

3. 在返回的 JSON 中：
   - `message.chat.id` 是 `TELEGRAM_CHAT_ID`
   - `message.from.id` 是 `TELEGRAM_TARGET_USER_ID`

## 重要说明

这个工作流使用 Telegram 的 `getUpdates`，所以这个 bot 不能同时启用 webhook。如果你之前设置过 webhook，需要先清除一次：

```text
https://api.telegram.org/bot<TOKEN>/deleteWebhook
```

如果同一个 bot token 还被其他长期运行的程序通过 polling / `getUpdates` 监听消息，本工作流仍然可以发送提醒，但检测回复可能会被跳过。最稳妥的做法是给这个提醒器单独使用一个 Telegram bot。

## 手动测试

进入：

`Actions` -> `FFXIV Telegram Reminder` -> `Run workflow`
