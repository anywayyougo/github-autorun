# github-autorun

把「定时/手动跑一段命令」和「把运行结果推送到通知渠道」封装成**一个可复用的 GitHub Actions 工作流**。任何仓库只要加一个十几行的调用文件，就能拥有「定时运行 + 结果通知」能力。

## 工作原理

```text
你的仓库 .github/workflows/daily.yml（schedule / 手动触发）
        |
        v
   uses: anywayyougo/github-autorun/.github/workflows/run-and-notify.yml@v1
        |
        v
   检出你的仓库 -> 检出 autorun 自身（锁定调用时的 SHA）
        -> 安装 Python / requirements.txt（uv 安装 + 云端缓存加速）
        -> 注入 Variables 和 Secrets 到运行环境
        -> 执行你的命令（输出全程留档）
        -> 上传 report.md（若存在）
        -> 按成功/失败状态推送通知
```

## 快速开始

1. 在你的仓库 `Settings -> Secrets and variables -> Actions` 中添加：
   - Secret `FEISHU_WEBHOOK_URL`：通知 webhook（也可换成钉钉/Slack/企微）
   - Secret `FEISHU_SIGN_SECRET`：webhook 签名密钥（可选）
   - 项目自身的密钥，如 `DEEPSEEK_API_KEY_MARKET`
   - Variable（非敏感配置），如 `QUANT_TARGET`
2. 新建 `.github/workflows/daily.yml`，内容照抄 [`examples/caller.yml`](examples/caller.yml)
3. push，或在 Actions 页面手动 Run workflow

## 调用参数（inputs）

| 名称 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `command` | string | 必填 | 要执行的命令（在调用方仓库检出目录中运行）|
| `notify-on` | string | `always` | 通知时机：`always` / `success` / `failure` / `never` |
| `channel` | string | `auto` | 渠道：`auto` / `feishu` / `dingtalk` / `slack` / `wecom` / `generic` |
| `title` | string | 空 | 通知标题，空则用调用方仓库名 |
| `working-directory` | string | `.` | 命令与 `requirements.txt` 所在目录 |
| `python-version` | string | `3.12` | Python 版本 |
| `timeout-minutes` | number | `30` | 任务超时 |
| `env-json` | string | `{}` | 额外环境变量的 JSON（推荐传 `${{ toJSON(vars) }}`）|

## Secrets

| 名称 | 必填 | 说明 |
|---|---|---|
| `webhook-url` | 否 | 通知 webhook 地址；为空时自动跳过通知，不报错 |
| `sign-secret` | 否 | 飞书/钉钉的签名密钥 |
| `env-secrets` | 否 | 项目密钥的 JSON 字符串，会作为环境变量注入 |

## 支持的通知渠道

`channel=auto`（默认）时按 webhook 域名自动识别，也可显式指定。

| 渠道 | webhook 域名 | 签名算法 |
|---|---|---|
| 飞书 自定义机器人 | `open.feishu.cn` / `larksuite` | `sign = Base64(HMAC-SHA256(key = timestamp + "\n" + secret, msg = ""))`，`timestamp`(秒) 与 `sign` 放 JSON body |
| 钉钉 自定义机器人 | `oapi.dingtalk.com` | `timestamp`(毫秒) + `sign`(Base64 后 URL 编码) 拼在 webhook URL 查询串 |
| Slack Incoming Webhook | `hooks.slack.com` | 无需签名 |
| 企业微信 群机器人 | `qyapi.weixin.qq.com` | 默认无需签名 |
| generic | 任意 | `POST` JSON：`{title, status, repository, run_url, text}` |

## 注意事项

- **个人账号不支持 `secrets: inherit`**：调用方必须用 `secrets:` 逐个传（见 examples）。
- **`schedule` 只能写在调用方仓库**：可复用工作流里写 `schedule` 不会生效。
- **依赖安装用 uv**：`requirements.txt` 存在时经 `astral-sh/setup-uv` 安装，包缓存持久化在 GitHub 云端（key 按依赖文件内容），首次冷装约半分钟、后续几秒；与本地电脑无关。
- 私有仓库也可以调用本公开工作流，无需额外 Access 设置（公开仓库被调用免授权）。
- `env-json: ${{ toJSON(vars) }}` 会把调用方仓库的全部 Variable 注入脚本环境；项目密钥请打包进 `env-secrets`。
- 版本调用建议 `@v1`（浮动 tag，向后兼容更新）；需要绝对稳定可改成具体 commit SHA。
- 若命令在 `working-directory` 下生成 `report.md`，会自动作为 artifact 上传。
- 通知失败（HTTP 非 200）会让 job 变红，便于及时发现；未配置 webhook 则自动跳过。

## 目录结构

见 [STRUCTURE.md](STRUCTURE.md)。

## License

MIT
