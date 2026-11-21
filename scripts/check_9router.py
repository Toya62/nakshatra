#!/usr/bin/env python3
"""
Nakshatra - 9router Health & Readiness Probe.
Verifies connection to 9router on port 20128, checks model catalog, and tests nakshatra-combo.
"""

import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_BASE_URL = os.environ.get("OPENAI_BASE_URL", "http://localhost:20128/v1").rstrip("/")
API_KEY = os.environ.get("OPENAI_API_KEY", "sk-296733e9c4d8e17e-zk5kkr-bc6339f4")
TARGET_MODEL = os.environ.get("OPENAI_MODEL", "nakshatra-combo")


def main() -> int:
    print(f"🔍 Probing 9router at {DEFAULT_BASE_URL}...")

    # Step 1: Health / Models Check
    req = urllib.request.Request(
        f"{DEFAULT_BASE_URL}/models",
        headers={"Authorization": f"Bearer {API_KEY}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("id") for m in data.get("data", [])]
            print(f"✅ 9router online. Found {len(models)} accessible model(s).")
            if TARGET_MODEL in models:
                print(f"✅ Target model '{TARGET_MODEL}' is active and ready.")
            else:
                print(f"ℹ️  Target model '{TARGET_MODEL}' will be routed dynamically.")
    except urllib.error.URLError as e:
        print(f"❌ Cannot connect to 9router at {DEFAULT_BASE_URL}: {e}")
        print("\nTroubleshooting:")
        print("  1. Start 9router in a terminal: 9router --skip-update -n -p 20128")
        print("  2. Or run: bash scripts/start_9router.sh")
        return 1

    # Step 2: Chat Completion Probe using OpenAI SDK
    print(f"🤖 Testing chat completion with model '{TARGET_MODEL}'...")
    try:
        from openai import OpenAI

        client = OpenAI(base_url=DEFAULT_BASE_URL, api_key=API_KEY)
        resp = client.chat.completions.create(
            model=TARGET_MODEL,
            messages=[{"role": "user", "content": "Say ping in 1 word"}],
            max_tokens=5,
            timeout=30.0,
        )
        content = resp.choices[0].message.content or "OK"
        print(f"✅ Model '{TARGET_MODEL}' responded successfully: {content.strip()}")
        print("🚀 9router is healthy and ready for Nakshatra AI consultations.")
        return 0
    except Exception as e:
        print(f"⚠️  Chat completion probe failed: {e}")
        print("Please check 9router credentials in ~/.9router/db/data.sqlite")
        return 1


if __name__ == "__main__":
    sys.exit(main())
