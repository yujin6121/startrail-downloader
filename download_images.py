import argparse
import os
import re
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlopen, Request

URL_RE = re.compile(r'https?://[^\s)\'\"]+')


def sanitize_filename(name: str) -> str:
    return name.replace("/", "_").replace("\\", "_")


def unique_path(path: str) -> str:
    base, ext = os.path.splitext(path)
    candidate = path
    i = 1
    while os.path.exists(candidate):
        candidate = f"{base}_{i}{ext}"
        i += 1
    return candidate


def load_env_file(path: str) -> None:
    if not path or not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            os.environ.setdefault(key, value)


def member_from_filename(filename: str) -> str:
    stem, _ext = os.path.splitext(filename)
    if stem.startswith("all-"):
        stem = stem[4:]
    stem = re.sub(r"-\d+$", "", stem)
    return sanitize_filename(stem or "unknown")


def classify_output_path(url: str, outdir: str, idx: int, organize: bool) -> str:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    name = os.path.basename(parsed.path) or f"file_{idx}"
    name = sanitize_filename(name)

    if not organize:
        return os.path.join(outdir, name)

    if len(parts) >= 2 and parts[-2] in ("wallpapers", "artworks"):
        category = parts[-2]
        member = member_from_filename(name)
        return os.path.join(outdir, member, category, name)

    if len(parts) >= 2 and parts[-2] == "audio":
        return os.path.join(outdir, "audio", name)

    return os.path.join(outdir, "assets", name)


def download(url: str, outdir: str, idx: int, organize: bool) -> bool:
    outpath = classify_output_path(url, outdir, idx, organize)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    outpath = unique_path(outpath)

    last_err = None
    for attempt in range(1, DOWNLOAD_RETRIES + 1):
        try:
            req = Request(url, headers=DEFAULT_HEADERS)
            with urlopen(req, timeout=30) as resp:
                data = resp.read()
            with open(outpath, "wb") as f:
                f.write(data)
            print(f"[OK] {url} -> {outpath}")
            return True
        except Exception as e:
            last_err = e
            if isinstance(e, HTTPError) and e.code == 404:
                hint = ""
                if "protected-artwork" in url and "Cookie" not in DEFAULT_HEADERS:
                    hint = " (protected URL: set STARTRAIL_COOKIE or pass --cookie)"
                print(f"[ERR] {url} : HTTP 404 Not Found{hint}")
                break
            if attempt < DOWNLOAD_RETRIES:
                time.sleep(RETRY_BACKOFF * attempt)
    err_path = os.path.join(outdir, "error_log.txt")
    with open(err_path, "a", encoding="utf-8") as ef:
        ef.write(f"{url} -> {last_err}\n")
    print(f"[ERR] {url} : {last_err} (logged to {err_path})")
    return False


def extract_urls_from_file(path: str):
    urls = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            for m in URL_RE.findall(line):
                urls.append(m.strip())
    return urls

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,audio/*,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": "https://startrail.stellive.me/",
}
DOWNLOAD_RETRIES = 1
RETRY_BACKOFF = 1


def main():
    p = argparse.ArgumentParser(description="Download URLs found in a text file")
    p.add_argument("file", nargs="?", default="download.txt", help="Input file containing URLs (default: download.txt)")
    p.add_argument("--outdir", "-o", default="downloads", help="Output directory (default: downloads)")
    p.add_argument("--env-file", default=".env", help="Env file to load before downloading (default: .env)")
    p.add_argument("--flat", action="store_true", help="Save all files directly in outdir instead of member folders.")
    p.add_argument("-H", "--header", action="append", help="Add request header (format: 'Key: Value'). Can be used multiple times.")
    p.add_argument("--cookie", help="Cookie header value. Defaults to STARTRAIL_COOKIE env var if set.")
    p.add_argument("--retries", type=int, default=1, help="Number of download retries (default: 1)")
    args = p.parse_args()

    load_env_file(args.env_file)

    if not os.path.exists(args.file):
        print(f"Input file not found: {args.file}")
        sys.exit(1)

    global DEFAULT_HEADERS, DOWNLOAD_RETRIES, RETRY_BACKOFF
    if args.header:
        for h in args.header:
            if ":" in h:
                k, v = h.split(":", 1)
                DEFAULT_HEADERS[k.strip()] = v.strip()
    cookie = args.cookie or os.environ.get("STARTRAIL_COOKIE")
    if cookie and "..." in cookie:
        cookie = ""
    if cookie:
        DEFAULT_HEADERS["Cookie"] = cookie.strip()
    DOWNLOAD_RETRIES = max(1, args.retries)

    urls = extract_urls_from_file(args.file)
    if not urls:
        print("No URLs found in the input file.")
        return

    os.makedirs(args.outdir, exist_ok=True)

    if any("protected-artwork" in url for url in urls) and "Cookie" not in DEFAULT_HEADERS:
        print("Protected artwork URLs detected. Set STARTRAIL_COOKIE or pass --cookie if these return 404.")

    print(f"Found {len(urls)} URLs. Downloading into '{args.outdir}'...")
    ok = 0
    failed = 0
    for i, url in enumerate(urls, start=1):
        if download(url, args.outdir, i, organize=not args.flat):
            ok += 1
        else:
            failed += 1
        time.sleep(0.1)
    print(f"Done. OK: {ok}, failed: {failed}")


if __name__ == "__main__":
    main()
