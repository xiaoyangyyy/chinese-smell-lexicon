# -*- coding: utf-8 -*-
"""Download materia medica texts and gazetteers."""
import json
import os
import subprocess
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = r"D:\qiwei\texts"
PROXY = "http://127.0.0.1:7897"

BENCAO = [
    "000-神农本草经.txt", "001-吴普本草.txt", "002-本草经集注.txt", "003-新修本草.txt",
    "004-食疗本草.txt", "005-海药本草.txt", "006-本草图经.txt", "007-本草衍义.txt",
    "008-汤液本草.txt", "009-饮膳正要.txt", "010-滇南本草.txt", "011-本草品汇精要.txt",
    "012-本草蒙筌.txt", "013-本草纲目.txt", "014-本草乘雅半偈.txt", "015-本草征要.txt",
    "016-本草易读.txt", "017-本草新编.txt", "018-本草备要.txt", "019-本经逢原.txt",
    "020-本草经解.txt", "021-本草从新.txt", "022-神农本草经百种录.txt", "023-本草纲目拾遗.txt",
    "024-本草崇原.txt", "025-本草求真.txt", "026-神农本草经读.txt", "027-本草述钩元.txt",
    "028-食鉴本草.txt", "029-本草思辨录.txt", "031-本草便读.txt", "032-本草撮要.txt",
    "033-本草问答.txt", "034-神农本草经赞.txt", "035-本草择要纲目.txt", "036-得配本草.txt",
    "037-本草害利.txt", "038-本草分经.txt", "050-名医别录.txt", "645-证类本草.txt",
]


def curl(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and os.path.getsize(dest) > 500:
        return "skip " + os.path.basename(dest)
    last = ""
    for _ in range(4):
        result = subprocess.run(
            [
                "curl.exe", "-sS", "--http1.1", "--ssl-no-revoke", "-f", "-L",
                "-x", PROXY, "--connect-timeout", "20", "--max-time", "180",
                "-o", dest, url,
            ],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if result.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 500:
            return "ok %s %d" % (os.path.basename(dest), os.path.getsize(dest))
        last = (result.stderr or "").strip()[:140]
        if os.path.exists(dest):
            os.remove(dest)
    return "FAIL %s %s" % (os.path.basename(dest), last)


def raw_url(repo, path):
    return "https://raw.githubusercontent.com/%s/master/%s" % (
        repo, urllib.parse.quote(path),
    )


def gazetteer_names():
    url = "https://api.github.com/repos/garychowcmu/daizhigev20/contents/" + urllib.parse.quote("史藏/地理")
    dest = r"D:\qiwei\_geo.json"
    line = curl(url, dest)
    if line.startswith("FAIL"):
        raise SystemExit(line)
    data = json.load(open(dest, encoding="utf-8"))
    names = []
    for item in data:
        name = item.get("name") or ""
        if name.endswith(".txt") and "志" in name:
            names.append(name)
    return names


def main():
    jobs = []
    for name in BENCAO:
        jobs.append((
            raw_url("xiaopangxia/TCM-Ancient-Books", name),
            os.path.join(ROOT, "本草", name),
        ))
    names = gazetteer_names()
    print("gazetteers", len(names), flush=True)
    for name in names:
        jobs.append((
            raw_url("garychowcmu/daizhigev20", "史藏/地理/" + name),
            os.path.join(ROOT, "方志", name),
        ))
    print("files", len(jobs), flush=True)
    failed = 0
    done = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(curl, url, dest) for url, dest in jobs]
        for future in as_completed(futures):
            line = future.result()
            done += 1
            if line.startswith("FAIL"):
                failed += 1
                print(line, flush=True)
            elif done % 15 == 0:
                print("%d/%d %s" % (done, len(jobs), line), flush=True)
    print("FINISHED failed", failed, flush=True)


if __name__ == "__main__":
    main()
