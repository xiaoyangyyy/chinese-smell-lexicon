# -*- coding: utf-8 -*-
"""Download the open poetry JSON files through the local proxy."""
import os
import subprocess
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = r"D:\qiwei\texts"
PROXY = "http://127.0.0.1:7897"
BASE = "https://raw.githubusercontent.com/chinese-poetry/chinese-poetry/master/"


def jobs():
    items = []
    for number in range(0, 58000, 1000):
        items.append("全唐诗/poet.tang.%d.json" % number)
    for number in range(0, 255000, 1000):
        items.append("全唐诗/poet.song.%d.json" % number)
    for number in range(0, 22000, 1000):
        items.append("宋词/ci.song.%d.json" % number)
    items.append("元曲/yuanqu.json")
    for name in [
        "huajianji-1-juan.json", "huajianji-2-juan.json", "huajianji-3-juan.json",
        "huajianji-4-juan.json", "huajianji-5-juan.json", "huajianji-6-juan.json",
        "huajianji-7-juan.json", "huajianji-8-juan.json", "huajianji-9-juan.json",
        "huajianji-x-juan.json",
    ]:
        items.append("五代诗词/huajianji/" + name)
    items.append("五代诗词/nantang/poetrys.json")
    return items


def fetch(rel):
    dest = os.path.join(ROOT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and os.path.getsize(dest) > 200:
        return "skip " + rel
    url = BASE + urllib.parse.quote(rel)
    last = ""
    for attempt in range(1, 6):
        result = subprocess.run(
            [
                "curl.exe", "-sS", "--http1.1", "--ssl-no-revoke", "-f", "-L",
                "-x", PROXY, "--connect-timeout", "20", "--max-time", "180",
                "-o", dest, url,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 200:
            return "ok %s %d" % (rel, os.path.getsize(dest))
        last = (result.stderr or "").strip()[:160]
        if os.path.exists(dest):
            os.remove(dest)
    return "FAIL %s %s" % (rel, last)


def main():
    todo = jobs()
    print("files", len(todo), flush=True)
    done = 0
    failed = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(fetch, rel) for rel in todo]
        for future in as_completed(futures):
            line = future.result()
            done += 1
            if line.startswith("FAIL"):
                failed += 1
            if done % 20 == 0 or line.startswith("FAIL"):
                print("%d/%d %s" % (done, len(todo), line), flush=True)
    print("FINISHED failed", failed, flush=True)


if __name__ == "__main__":
    main()
