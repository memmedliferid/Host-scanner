import requests
import os
from datetime import datetime, timezone

TELEGRAM_TOKEN = "8811650010:AAF3qAKekoObZInM2NQavrc4YfnakHUBF7A"
CHAT_ID = "1436101177"

DOMAINS = [
    "nar.az",
    "azercell.com"
]

CACHE_FILE = "hosts_cache.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        r = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": text
            },
            timeout=20
        )

        print("Telegram:", r.status_code, r.text[:300])
        return r.ok

    except Exception as e:
        print("Telegram xətası:", e)
        return False


def normalize(host, domain):
    host = host.strip().lower().rstrip(".")

    if host.startswith("*."):
        host = host[2:]

    if host == domain or host.endswith("." + domain):
        return host

    return None


def crtsh(domain):
    result = set()

    try:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        r = requests.get(url, headers=HEADERS, timeout=30)

        if r.status_code == 200:
            for item in r.json():
                for name in item.get("name_value", "").splitlines():
                    host = normalize(name, domain)
                    if host:
                        result.add(host)

    except Exception as e:
        print("crt.sh:", e)

    return result


def hackertarget(domain):
    result = set()

    try:
        url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
        r = requests.get(url, headers=HEADERS, timeout=30)

        if r.status_code == 200:
            for line in r.text.splitlines():
                if "," in line:
                    host = normalize(line.split(",", 1)[0], domain)
                    if host:
                        result.add(host)

    except Exception as e:
        print("HackerTarget:", e)

    return result


def alienvault(domain):
    result = set()

    try:
        url = (
            "https://otx.alienvault.com/"
            f"api/v1/indicators/domain/{domain}/passive_dns"
        )

        r = requests.get(url, headers=HEADERS, timeout=30)

        if r.status_code == 200:
            for item in r.json().get("passive_dns", []):
                host = normalize(
                    item.get("hostname", ""),
                    domain
                )

                if host:
                    result.add(host)

    except Exception as e:
        print("AlienVault:", e)

    return result


def anubis(domain):
    result = set()

    try:
        url = f"https://jldc.me/anubis/subdomains/{domain}"
        r = requests.get(url, headers=HEADERS, timeout=30)

        if r.status_code == 200:
            for name in r.json():
                host = normalize(name, domain)

                if host:
                    result.add(host)

    except Exception as e:
        print("Anubis:", e)

    return result


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return set()

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return {
            line.strip()
            for line in f
            if line.strip()
        }


def save_cache(hosts):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        for host in sorted(hosts):
            f.write(host + "\n")


def scan():
    all_hosts = set()

    for domain in DOMAINS:
        print(f"\n[+] {domain}")

        all_hosts.update(crtsh(domain))
        all_hosts.update(hackertarget(domain))
        all_hosts.update(alienvault(domain))
        all_hosts.update(anubis(domain))

    return all_hosts


def main():

    print("[+] Scanner başladı")

    # Telegram bağlantısını yoxla
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "BURA_TOKENI_YAZ":
        print("Token yazılmayıb.")
        return

    current = scan()
    old = load_cache()

    new = current - old

    now = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    print("Ümumi:", len(current))
    print("Yeni:", len(new))

    # İlk dəfə işləyirsə, bütün mövcud nəticələri göndər
    if not old:
        report = [
            "🔎 SUBDOMAIN SCAN",
            f"Vaxt: {now}",
            "",
            f"Tapılan subdomain: {len(current)}",
            ""
        ]

        report.extend(
            f"• {host}"
            for host in sorted(current)
        )

    elif new:
        report = [
            "🆕 YENİ SUBDOMAINLƏR",
            f"Vaxt: {now}",
            "",
            f"Yeni: {len(new)}",
            f"Ümumi: {len(current)}",
            ""
        ]

        report.extend(
            f"• {host}"
            for host in sorted(new)
        )

    else:
        report = [
            "✅ SCAN TAMAMLANDI",
            f"Vaxt: {now}",
            "",
            "Yeni subdomain tapılmadı.",
            f"Ümumi məlum subdomain: {len(current)}"
        ]

    message = "\n".join(report)

    # Telegram mesajlarını hissələrə böl
    while message:

        part = message[:3800]

        if len(message) > 3800:
            cut = part.rfind("\n")

            if cut > 0:
                part = message[:cut]

        send_telegram(part)

        message = message[len(part):].lstrip()

    save_cache(current)

    print("[+] Bitdi")


if __name__ == "__main__":
    main()
