"""Quick Resend deliverability test (local diagnostic — safe to delete).

Run it WITHOUT putting your key in any file:

    PowerShell:
        $env:RESEND_API_KEY="re_your_key_here"; python send_test.py

It sends one test email using the same from/to as the website and prints the
FULL Resend response, so any problem (bad key, unverified domain, etc.) is shown.
"""
import json
import os
import urllib.error
import urllib.request

API_KEY = os.environ.get("RESEND_API_KEY", "")
CONTACT_TO = os.environ.get("CONTACT_TO", "inquiry@kalibratesolutions.com")
CONTACT_FROM = os.environ.get(
    "CONTACT_FROM", "KSA Metrology Website <inquiry@kalibratesolutions.com>")

if not API_KEY:
    raise SystemExit("RESEND_API_KEY is not set. Set it first, then re-run.")

payload = {
    "from": CONTACT_FROM,
    "to": [CONTACT_TO],
    "subject": "KSA website — Resend test email",
    "text": "This is a test from send_test.py. If you see this, delivery works.",
}
req = urllib.request.Request(
    "https://api.resend.com/emails",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Authorization": f"Bearer {API_KEY}",
             "Content-Type": "application/json",
             "User-Agent": "KSA-Website/1.0",
             "Accept": "application/json"},
    method="POST",
)
print(f"from: {CONTACT_FROM}")
print(f"to:   {CONTACT_TO}")
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        print(f"\nHTTP {resp.status} — SUCCESS")
        print(resp.read().decode("utf-8", "ignore"))
except urllib.error.HTTPError as exc:
    print(f"\nHTTP {exc.code} — FAILED")
    print(exc.read().decode("utf-8", "ignore"))
except Exception as exc:  # noqa: BLE001
    print(f"\nERROR: {exc}")
