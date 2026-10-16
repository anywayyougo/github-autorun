#!/usr/bin/env python3
"""Send a workflow run summary to a webhook."""

import base64
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

TAIL_CHARS = 3000
TIMEOUT = 20


def env(name, default=""):
    return os.environ.get(name) or default


def detect_channel(url):
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    if "feishu" in host or "larksuite" in host:
        return "feishu"
    if "dingtalk" in host:
        return "dingtalk"
    if "slack" in host:
        return "slack"
    if "weixin" in host or "wecom" in host:
        return "wecom"
    return "generic"


def read_tail(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            data = handle.read().strip()
    except OSError:
        return ""
    if len(data) > TAIL_CHARS:
        data = "... (truncated)\n" + data[-TAIL_CHARS:]
    return data


def build_text(title, status):
    repo = env("GITHUB_REPOSITORY", "unknown/unknown")
    server = env("GITHUB_SERVER_URL", "https://github.com")
    run_id = env("GITHUB_RUN_ID", "")
    run_url = f"{server}/{repo}/actions/runs/{run_id}" if run_id else server
    labels = {"success": "SUCCEEDED", "failure": "FAILED", "cancelled": "CANCELLED"}
    label = labels.get(status, status.upper())
    lines = [
        f"[{title}] RUN {label}",
        f"Repository: {repo}",
        f"Workflow: {env('GITHUB_WORKFLOW', '-')}",
        f"Actor: {env('GITHUB_ACTOR', '-')}",
        f"Run: {run_url}",
    ]
    tail = read_tail(env("AUTORUN_LOG"))
    if tail:
        lines.append("---- output ----")
        lines.append(tail)
    return "\n".join(lines)


def post_json(url, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            text = response.read(500).decode("utf-8", "replace")
            print(f"[notify] HTTP {response.status}: {text}")
            return response.status < 400
    except urllib.error.HTTPError as error:
        detail = error.read(500).decode("utf-8", "replace")
        print(f"[notify] HTTP {error.code}: {detail}")
        return False
    except Exception as error:
        print(f"[notify] request failed: {error}")
        return False


def send_feishu(url, secret, text):
    payload = {"msg_type": "text", "content": {"text": text}}
    if secret:
        timestamp = str(int(time.time()))
        string_to_sign = f"{timestamp}\n{secret}"
        digest = hmac.new(string_to_sign.encode("utf-8"), b"", hashlib.sha256).digest()
        payload["timestamp"] = timestamp
        payload["sign"] = base64.b64encode(digest).decode("utf-8")
    return post_json(url, payload)


def send_dingtalk(url, secret, text):
    if secret:
        timestamp = str(int(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{secret}"
        digest = hmac.new(
            secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(digest).decode("utf-8"))
        joiner = "&" if "?" in url else "?"
        url = f"{url}{joiner}timestamp={timestamp}&sign={sign}"
    return post_json(url, {"msgtype": "text", "text": {"content": text}})


def send_slack(url, secret, text):
    return post_json(url, {"text": text})


def send_wecom(url, secret, text):
    return post_json(url, {"msgtype": "text", "text": {"content": text}})


def send_generic(url, secret, text):
    server = env("GITHUB_SERVER_URL", "https://github.com")
    repo = env("GITHUB_REPOSITORY")
    run_id = env("GITHUB_RUN_ID")
    payload = {
        "title": env("AUTORUN_TITLE"),
        "status": env("AUTORUN_JOB_STATUS", "unknown"),
        "repository": repo,
        "run_url": f"{server}/{repo}/actions/runs/{run_id}",
        "text": text,
    }
    return post_json(url, payload)


SENDERS = {
    "feishu": send_feishu,
    "dingtalk": send_dingtalk,
    "slack": send_slack,
    "wecom": send_wecom,
    "generic": send_generic,
}


def should_notify(notify_on, status):
    if notify_on == "never":
        return False
    if notify_on == "success":
        return status == "success"
    if notify_on == "failure":
        return status != "success"
    return True


def main():
    notify_on = env("AUTORUN_NOTIFY_ON", "always").strip().lower()
    status = env("AUTORUN_JOB_STATUS", "success").strip().lower()
    if not should_notify(notify_on, status):
        print(f"[notify] skipped (notify-on={notify_on}, status={status})")
        return 0

    url = env("WEBHOOK_URL").strip()
    if not url:
        print("[notify] skipped (no webhook configured)")
        return 0

    secret = env("SIGN_SECRET").strip()
    channel = env("AUTORUN_CHANNEL", "auto").strip().lower()
    if channel in ("", "auto"):
        channel = detect_channel(url)

    title = env("AUTORUN_TITLE").strip() or env("GITHUB_REPOSITORY", "run")
    text = build_text(title, status)

    sender = SENDERS.get(channel, send_generic)
    print(f"[notify] channel={channel}")
    ok = sender(url, secret, text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
