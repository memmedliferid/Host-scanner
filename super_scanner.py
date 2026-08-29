import requests
import os

TELEGRAM_TOKEN = "8811650010:AAFGCoQ5rMLmu4AjgjxxGeaNQ60WaTVpXeY"
CHAT_ID = "1436101177"

DOMAINS = [
    "nar.az",
    "azercell.com"
]

CACHE_FILE = "hosts_cache.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def send_telegram(message):
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "8811650010:AAFGCoQ5rMLmu4AjgjxxGeaNQ60WaTVpXeY":
        print("Telegram token yazılmayıb!")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=20
        )

        print("Telegram:", response.status_code)

    except Exception as e:
        print("Telegram xətası:", e)


def normalize_host(host, domain):
    host = host.strip().lower().rstrip(".")

    if host.startswith("*."):
        host = host[2:]

    if host == domain or host.endswith("." + domain):
        return host

    return None


def get_crtsh(domain):
    results = set()

    try:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        if response.status_code == 200:
            for item in response.json():

                names = item.get("name_value", "")

                for name in names.splitlines():

                    host = normalize_host(name, domain)

                    if host:
                        results.add(host)

    except Exception as e:
        print("crt.sh xətası:", e)

    return results


def get_hackertarget(domain):
    results = set()

    try:
        url = f"https://api.hackertarget.com/hostsearch/?q={domain}"

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        if response.status_code == 200:

            for line in response.text.splitlines():

                if "," not in line:
                    continue

                host = line.split(",", 1)[0]

                host = normalize_host(host, domain)

                if host:
                    results.add(host)

    except Exception as e:
        print("HackerTarget xətası:", e)

    return results


def get_alienvault(domain):
    results = set()

    try:
        url = (
            "https://otx.alienvault.com/"
            f"api/v1/indicators/domain/{domain}/passive_dns"
        )

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        if response.status_code == 200:

            data = response.json()

            for item in data.get("passive_dns", []):

                host = item.get("hostname", "")

                host = normalize_host(host, domain)

                if host:
                    results.add(host)

    except Exception as e:
        print("AlienVault xətası:", e)

    return results


def get_anubis(domain):
    results = set()

    try:
        url = f"https://jldc.me/anubis/subdomains/{domain}"

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        if response.status_code == 200:

            for name in response.json():

                host = normalize_host(name, domain)

                if host:
                    results.add(host)

    except Exception as e:
        print("Anubis xətası:", e)

    return results


def load_cache():

    if not os.path.exists(CACHE_FILE):
        return set()

    try:

        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return {
                line.strip().lower()
                for line in file
                if line.strip()
            }

    except Exception:
        return set()


def save_cache(hosts):

    with open(
        CACHE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        for host in sorted(hosts):
            file.write(host + "\n")


def scan_domain(domain):

    results = set()

    print(f"\n[+] {domain} yoxlanılır...")

    results.update(get_crtsh(domain))
    results.update(get_hackertarget(domain))
    results.update(get_alienvault(domain))
    results.update(get_anubis(domain))

    print(
        f"[+] {domain}: "
        f"{len(results)} subdomain tapıldı"
    )

    return results


def main():

    print("=" * 55)
    print("       PASSİV SUBDOMAIN SCANNER")
    print("=" * 55)

    current_hosts = set()

    for domain in DOMAINS:

        hosts = scan_domain(domain)

        current_hosts.update(hosts)

    old_hosts = load_cache()

    new_hosts = current_hosts - old_hosts

    print()
    print(f"Ümumi subdomain: {len(current_hosts)}")
    print(f"Əvvəlki nəticə: {len(old_hosts)}")
    print(f"Yeni subdomain: {len(new_hosts)}")

    if new_hosts:

        lines = [
            "🆕 YENİ SUBDOMAINLƏR",
            "",
            f"Ümumi: {len(current_hosts)}",
            f"Yeni: {len(new_hosts)}",
            ""
        ]

        for host in sorted(new_hosts):

            lines.append(
                f"• {host}"
            )

        message = "\n".join(lines)

        while len(message) > 3800:

            cut = message.rfind(
                "\n",
                0,
                3800
            )

            if cut <= 0:
                cut = 3800

            send_telegram(
                message[:cut]
            )

            message = message[cut:].lstrip()

        if message:
            send_telegram(message)

    else:

        print("Yeni subdomain tapılmadı.")

    save_cache(current_hosts)

    print("\n[+] İş tamamlandı.")


if __name__ == "__main__":
    main()
