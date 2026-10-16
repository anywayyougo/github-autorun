#!/usr/bin/env python3
"""Inject JSON encoded environment bundles into GITHUB_ENV."""

import json
import os
import uuid


def append(name, value):
    with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as handle:
        if "\n" in value or "\r" in value:
            delimiter = f"ghadelimiter_{uuid.uuid4().hex}"
            handle.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")
        else:
            handle.write(f"{name}={value}\n")


def load(source):
    raw = os.environ.get(source) or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        print(f"[load_env] {source} is not valid JSON: {error}")
        return 0
    if not isinstance(data, dict):
        print(f"[load_env] {source} is not a JSON object, skipped")
        return 0
    count = 0
    for key, value in data.items():
        if value is None or value == "":
            continue
        append(str(key), str(value))
        count += 1
    return count


def main():
    total = load("VAR_JSON") + load("SECRET_JSON")
    print(f"[load_env] injected {total} variable(s)")


if __name__ == "__main__":
    main()
