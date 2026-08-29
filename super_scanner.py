import requests
import socket
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TELEGRAM_TOKEN = "8633891826:AAGwlt8LIOK0aiByAyQDmw23q21bsmeAm28"
CHAT_ID = "1436101177"
DOMAINS = ["nar.az", "azercell.com"]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram xətası: {e}")

def get_crtsh_subdomains(domain):
    subdomains = set()
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            data = response.json()
            for entry in data:
                name_value = entry.get('name_value', '')
                for sub in name_value.split('\n'):
                    sub = sub.strip().lower()
                    if sub.endswith(domain) and '*' not in sub:
                        subdomains.add(sub)
    except Exception:
        pass
    return subdomains

def get_hackertarget_subdomains(domain):
    subdomains = set()
    url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200 and "API count exceeded" not in response.text:
            for line in response.text.split('\n'):
                if ',' in line:
                    sub = line.split(',')[0].strip().lower()
                    if sub.endswith(domain):
                        subdomains.add(sub)
    except Exception:
        pass
    return subdomains

def check_host_status(host):
    try:
        res = requests.get(f"https://{host}", timeout=3, verify=False)
        if res.status_code < 400:
            return f"HTTP {res.status_code} (Aktiv)"
    except:
        try:
            socket.gethostbyname(host)
            return "DNS Açıq"
        except:
            pass
    return None

if __name__ == "__main__":
    print("[🔥] Host Scanner işə düşdü...")
    current_hosts = set()
    
    for dom in DOMAINS:
        current_hosts.update(get_crtsh_subdomains(dom))
        current_hosts.update(get_hackertarget_subdomains(dom))
    
    report_lines = [f"📊 *Nar və Azercell Host Hesabatı*\nÜmumi tapılan: {len(current_hosts)}\n"]
    
    active_count = 0
    for host in sorted(current_hosts):
        status = check_host_status(host)
        if status:
            active_count += 1
            if active_count <= 30:
                report_lines.append(f"• `{host}` -> {status}")

    msg = "\n".join(report_lines)
    if len(msg) > 4000:
        msg = msg[:3900] + "\n...(çoxluq səbəbindən kəsildi)"
        
    send_telegram(msg)
    print("[*] Hesabat Telegram-a göndərildi.")
    
