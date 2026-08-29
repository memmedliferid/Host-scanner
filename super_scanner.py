import requests
import socket
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TELEGRAM_TOKEN = "8811650010:AAFGCoQ5rMLmu4AjgjxxGeaNQ60WaTVpXeY"
CHAT_ID = "1436101177"

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

    try:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        response = requests.get(url, timeout=20)

        if response.status_code == 200:
            for entry in response.json():
                for sub in entry.get("name_value", "").split("\n"):
                    sub = sub.strip().lower()

                    if sub.endswith(domain) and "*" not in sub:
                        subdomains.add(sub)
        else:
            print(f"crt.sh HTTP xətası: {response.status_code}")

    except Exception as e:
        print(f"crt.sh xətası: {e}")

    return subdomains


def get_hackertarget_subdomains(domain):
    subdomains = set()

    try:
        url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
        response = requests.get(url, timeout=15)

        if response.status_code == 200:
            for line in response.text.splitlines():

                if "," in line:
                    sub = line.split(",")[0].strip().lower()

                    if sub.endswith(domain):
                        subdomains.add(sub)

        else:
            print(f"HackerTarget HTTP xətası: {response.status_code}")

    except Exception as e:
        print(f"HackerTarget xətası: {e}")

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

        print(f"[*] {domain} axtarılır...")

        current_hosts.update(
            get_crtsh_subdomains(domain)
        )

        current_hosts.update(
            get_hackertarget_subdomains(domain)
        )

    print(f"[*] Tapılan host sayı: {len(current_hosts)}")

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

    message = "\n".join(report_lines)

    if len(message) > 4000:
        message = message[:3900] + "\n...(hesabat kəsildi)"

    send_telegram(message)

    print("[*] Hesabat Telegram-a göndərildi.")
