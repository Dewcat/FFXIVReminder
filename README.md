# FFXIVReminder

基于 GitHub Actions 的 Telegram 提醒器。

## 功能说明

每天 **Asia/Shanghai 时区 20:00**，工作流会检查目标 Telegram 用户本月是否已经回复过。

- 每个月第一次运行时，会发送：`记得上号保部队房`
- 如果目标用户还没有回复，它会每天 20:00 继续发送同样的消息。
- 一旦目标用户在私聊中回复了任意文字消息，它就会发送：`收到，下个月初再提醒你`，并停止发送提醒，直到下个月。
- 群聊或超群里的消息不会被当作确认回复。
- 到下个月时，提醒周期会自动重置。

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
| `REMINDER_MESSAGE` | `记得上号保部队房` |
| `ACK_MESSAGE` | `收到，下个月初再提醒你` |
| `REMINDER_TIMEZONE` | `Asia/Shanghai` |

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
