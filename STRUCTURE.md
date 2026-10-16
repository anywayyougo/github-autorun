# 项目结构

> 一句话定位：把「定时跑命令 + 结果通知」封装成一个可复用工作流，供任意仓库调用。

## 目录树

```text
github-autorun/
├─ .github/workflows/
│  ├─ run-and-notify.yml   # 核心：被调用的可复用工作流
│  └─ selftest.yml         # 自测：push 时用本地路径调用核心工作流，验证全链路
├─ scripts/
│  ├─ notify.py            # 多渠道通知（飞书/钉钉/Slack/企微/通用 webhook）
│  └─ load_env.py          # 把 env-json / env-secrets 注入到运行环境
├─ examples/
│  └─ caller.yml           # 调用方模板：复制到你的仓库、改两行即可
├─ README.md               # 使用说明：参数、密钥、渠道、注意事项
├─ STRUCTURE.md            # 本文件：结构、职责、流程
├─ RENAMING_THIS_REPO_BREAKS_ALL_CALLERS.md   # 警告：改仓库名会中断所有调用方
├─ LICENSE                 # MIT
└─ .gitignore
```

## 每部分功能

| 文件 | 作用 | 谁在何时执行 | 关键点 |
|---|---|---|---|
| `.github/workflows/run-and-notify.yml` | 核心可复用工作流：检出代码、装依赖、注入变量、执行命令、上传产物、推送通知 | 被调用方仓库通过 `uses:` 触发（`workflow_call`）| 全部能力的入口；输入 8 个、Secrets 3 个 |
| `.github/workflows/selftest.yml` | 冒烟自测：push 到 main 或手动触发，用**相对路径**调用核心工作流 | 本仓库 push / 手动 | 验证：自检出、环境注入、命令执行、日志留档 |
| `scripts/notify.py` | 组装消息并按渠道推送；无 webhook 时静默跳过；HTTP 失败返回非零 | 核心工作流最后一步（`always()`）| 纯标准库；`channel=auto` 按域名识别；读日志尾部 3000 字符 |
| `scripts/load_env.py` | 解析 `env-json` / `env-secrets` 两个 JSON，写入 `$GITHUB_ENV` | 核心工作流「Load environment」步骤 | 纯标准库；多行值用 heredoc 分隔符安全写入 |
| `examples/caller.yml` | 调用方模板，演示 schedule + 手动触发 + 参数/密钥写法 | 用户复制到自己的仓库 | 是「怎么用」的最短示例 |
| `README.md` | 面向使用者：快速开始、参数表、渠道配置、限制 | 人类阅读 | |
| `STRUCTURE.md` | 面向维护者：结构、职责、流程、改哪里 | 人类阅读 | 本文件 |
| `RENAMING_THIS_REPO_BREAKS_ALL_CALLERS.md` | 警告：仓库名被调用方硬编码，改名即中断 | 人类维护前阅读 | 文件名即为提醒 |
| `LICENSE` / `.gitignore` | 许可与忽略规则 | | MIT |

## 运行流程

```text
调用方仓库
  ├─ schedule（cron，写在调用方）/ workflow_dispatch / push ...
  └─ job: uses run-and-notify.yml@v1
        │
        ▼
  run-and-notify.yml（本仓库）
   ① checkout 调用方仓库（默认 workspace）
   ② checkout 本仓库自身到 .autorun/（repository=${{ job.workflow_repository }}, ref=${{ job.workflow_sha }}）
   ③ setup-python
   ④ 有 requirements.txt 则用 uv 安装（setup-uv，enable-cache 云端缓存）
   ⑤ load_env.py：env-json + env-secrets → $GITHUB_ENV
   ⑥ 执行 command（pipefail + tee 到固定日志文件）
   ⑦ 上传 working-directory/report.md 为 artifact（存在才传）
   ⑧ notify.py：读 job.status + 日志尾部 → 推送通知（未配 webhook 则跳过）
```

## 数据流

- **Variables（非敏感）**：调用方 `vars` 经 `env-json: ${{ toJSON(vars) }}` 传入 → `load_env.py` 注入 → 命令可见（如 `QUANT_TARGET`）。
- **Secrets（敏感）**：调用方逐个经 `secrets:` 传入 → 其中项目密钥用 `env-secrets`(JSON) 打包，通知相关用 `webhook-url` / `sign-secret`。
- **本仓库脚本**：不从调用方 workspace 读取，而是从 `.autorun/scripts/` 读取（`job.workflow_sha` 锁定版本，tag 漂移也不影响）。

## 改哪里

- 改通知文案/格式或新增渠道 → `scripts/notify.py`
- 新增/修改工作流参数、步骤顺序 → `.github/workflows/run-and-notify.yml`
- 改调用示例或默认值说明 → `examples/caller.yml` / `README.md`
- 本结构变化 → 本文件 `STRUCTURE.md`
