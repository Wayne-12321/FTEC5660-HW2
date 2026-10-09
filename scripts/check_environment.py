"""Check the prescribed provider/model without displaying credentials."""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    for line in (root / ".env").read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
    request = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps({"model": "deepseek-v4-flash", "temperature": 0,
                         "max_tokens": 12,
                         "messages": [{"role": "user", "content": "Reply with OK."}]}).encode(),
        headers={"Authorization": "Bearer " + os.environ["DEEPSEEK_API_KEY"],
                 "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.load(response)
        print("Provider call succeeded. Model:", result.get("model"))
        print("Usage:", json.dumps(result.get("usage", {})))
        return 0
    except urllib.error.HTTPError as exc:
        error = json.loads(exc.read()).get("error", {})
        print("Provider HTTP status:", exc.code)
        print("Provider error type:", error.get("type"))
        print("Provider error code:", error.get("code"))
        return 1
    except Exception as exc:
        print("Provider call failed:", type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
