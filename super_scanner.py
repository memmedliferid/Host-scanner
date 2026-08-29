import requests
import socket
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

DOMAINS = ["nar.az", "azercell.com"]


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=15
        )

        print("Telegram HTTP:", response.status_code)
        print("Telegram cavabı:", response.text)

    except Exception as e:
        print("Telegram xətası:", e)


def get_crtsh_subdomains(domain):
    subdomains = set()
    url = f"https://crt.sh/?q=%25.{domain}&output=json"

    try:
        response = requests.get(url, timeout=20)

        if response.status_code == 200:
            data = response.json()

            for entry in data:
                name_value = entry.get("name_value", "")

                for sub in name_value.split("\n"):
                    sub = sub.strip().lower()

                    if sub.endswith(domain) and "*" not in sub:
                        subdomains.add(sub)
        else:
            print(f"crt.sh HTTP xətası: {response.status_code}")

    except Exception as e:
        print(f"crt.sh xətası ({domain}): {e}")

    return subdomains


def get_hackertarget_subdomains(domain):
    subdomains = set()
    url = f"https://api.hackertarget.com/hostsearch/?q={domain}"

    try:
        response = requests.get(url, timeout=15)

        if response.status_code == 200:
            if "API count exceeded" not in response.text:

                for line in response.text.splitlines():

                    if "," in line:
                        sub = line.split(",")[0].strip().lower()

                        if sub.endswith(domain):
                            subdomains.add(sub)

            else:
                print(f"HackerTarget API limiti dolub: {domain}")

        else:
            print(
                f"HackerTarget HTTP xətası "
                f"({domain}): {response.status_code}"
            )

    except Exception as e:
        print(f"HackerTarget xətası ({domain}): {e}")

    return subdomains


def check_host_status(host):
    try:
        response = requests.get(
            f"https://{host}",
            timeout=5,
            verify=False
        )

        if response.status_code < 400:
            return f"HTTP {response.status_code} (Aktiv)"

        return f"HTTP {response.status_code}"

    except Exception:

        try:
            socket.gethostbyname(host)
            return "DNS Açıq"

        except Exception:
            return None


if __name__ == "__main__":

    print("[*] Host Scanner işə düşdü...")

    current_hosts = set()

    for domain in DOMAINS:

        print(f"[*] {domain} üçün subdomainlər axtarılır...")

        current_hosts.update(
            get_crtsh_subdomains(domain)
        )

        current_hosts.update(
            get_hackertarget_subdomains(domain)
        )

    print(
        f"[*] Ümumi tapılan host sayı: "
        f"{len(current_hosts)}"
    )

    report_lines = [
        "Nar və Azercell Host Hesabatı",
        f"Ümumi tapılan: {len(current_hosts)}",
        ""
    ]

    active_count = 0

    for host in sorted(current_hosts):

        status = check_host_status(host)

        if status:

            active_count += 1

            if active_count <= 30:
                report_lines.append(
                    f"- {host} -> {status}"
                )

    report_lines.insert(
        2,
        f"Aktiv host sayı: {active_count}"
    )

    msg = "\n".join(report_lines)

    if len(msg) > 4000:
        msg = msg[:3900] + "\n...(hesabat kəsildi)"

    send_telegram(msg)

    print("[*] Hesabat Telegram-a göndərildi.")
