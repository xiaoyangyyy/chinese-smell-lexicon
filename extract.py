# -*- coding: utf-8 -*-
"""Extract smell-word records from poetry, materia medica, and gazetteers."""
import csv
import json
import os
import random
import re
import sys
from collections import defaultdict

from lexicon import PLACES, SEASONS, SENSES, WORDS
from tradmap import to_trad

ROOT = r"D:\qiwei"
CORPUS = os.path.join(ROOT, "texts")
OUT = os.path.join(ROOT, "data")
CSV_PATH = os.path.join(OUT, "气味词典.csv")
SAMPLE_PATH = os.path.join(OUT, "抽查1000.csv")

SOURCES = [
    (os.path.join(CORPUS, "全唐诗"), "全唐诗", "唐", "poet.tang."),
    (os.path.join(CORPUS, "全唐诗"), "全宋诗", "宋", "poet.song."),
    (os.path.join(CORPUS, "宋词"), "全宋词", "宋", None),
    (os.path.join(CORPUS, "元曲"), "元曲", "元", None),
    (os.path.join(CORPUS, "五代诗词"), "五代诗词", "五代", None),
]


def both(text):
    forms = {text, to_trad(text)}
    return [item for item in forms if item]


def build_index():
    index = defaultdict(list)
    seen = set()
    for simp, category, obj in WORDS:
        for form in both(simp):
            if form in seen:
                continue
            seen.add(form)
            index[form[0]].append((form, simp, category, obj))
    for key in index:
        index[key].sort(key=lambda item: len(item[0]), reverse=True)
    return index, len(seen)


def build_places():
    pairs = []
    seen = set()
    for name in PLACES:
        simp = name
        for form in both(name):
            if form in seen or len(form) < 2:
                continue
            seen.add(form)
            pairs.append((form, simp))
    pairs.sort(key=lambda item: len(item[0]), reverse=True)
    return pairs


def build_seasons():
    pairs = []
    seen = set()
    for token, season in SEASONS:
        for form in both(token):
            if (form, season) in seen:
                continue
            seen.add((form, season))
            pairs.append((form, season))
    pairs.sort(key=lambda item: len(item[0]), reverse=True)
    return pairs


def build_senses():
    pairs = []
    seen = set()
    for token, label in SENSES.items():
        for form in both(token):
            if form in seen:
                continue
            seen.add(form)
            pairs.append((form, label))
    pairs.sort(key=lambda item: len(item[0]), reverse=True)
    return pairs


def find_words(line, index):
    hits = []
    i = 0
    n = len(line)
    while i < n:
        found = None
        for form, simp, category, obj in index.get(line[i], ()):
            if line.startswith(form, i):
                found = (simp, category, obj, i, i + len(form))
                break
        if found:
            hits.append(found)
            i = found[4]
        else:
            i += 1
    return hits


def find_labels(line, pairs):
    labels = []
    seen = set()
    for form, label in pairs:
        if form in line and label not in seen:
            seen.add(label)
            labels.append(label)
    return labels


def works_in(path):
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("content", "works", "data", "poems"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def title_of(work):
    return work.get("title") or work.get("rhythmic") or work.get("name") or ""


def paragraphs_of(work):
    paragraphs = work.get("paragraphs") or work.get("content") or []
    if isinstance(paragraphs, str):
        return [line for line in paragraphs.splitlines() if line.strip()]
    return [line for line in paragraphs if isinstance(line, str) and line.strip()]


def files_for(folder, prefix):
    if not os.path.isdir(folder):
        return []
    names = []
    for dirpath, _, filenames in os.walk(folder):
        for name in filenames:
            if not name.endswith(".json"):
                continue
            if prefix and not name.startswith(prefix):
                continue
            if name.startswith("author"):
                continue
            names.append(os.path.join(dirpath, name))
    return sorted(names)


BENCAO_ERA = {
    "神农本草经": "汉",
    "吴普本草": "魏",
    "本草经集注": "梁",
    "名医别录": "梁",
    "新修本草": "唐",
    "食疗本草": "唐",
    "海药本草": "五代",
    "本草图经": "宋",
    "本草衍义": "宋",
    "证类本草": "宋",
    "汤液本草": "元",
    "饮膳正要": "元",
    "滇南本草": "明",
    "本草品汇精要": "明",
    "本草蒙筌": "明",
    "本草纲目": "明",
    "本草乘雅半偈": "明",
    "本草征要": "明",
    "本草易读": "清",
    "本草新编": "清",
    "本草纲目拾遗": "清",
    "本经逢原": "清",
    "本草经解": "清",
    "神农本草经百种录": "清",
    "神农本草经读": "清",
    "本草述钩元": "清",
    "食鉴本草": "明",
    "本草思辨录": "清",
    "本草便读": "清",
    "本草撮要": "清",
    "本草问答": "清",
    "神农本草经赞": "清",
    "本草择要纲目": "清",
    "得配本草": "清",
    "本草害利": "清",
    "本草分经": "清",
    "本草备要": "清",
    "本草从新": "清",
    "本草求真": "清",
    "本草崇原": "清",
}


REIGN_ERA = (
    ("顺治", "清"), ("康熙", "清"), ("雍正", "清"), ("乾隆", "清"), ("嘉庆", "清"),
    ("道光", "清"), ("咸丰", "清"), ("同治", "清"), ("光绪", "清"), ("宣统", "清"),
    ("洪武", "明"), ("建文", "明"), ("永乐", "明"), ("洪熙", "明"), ("宣德", "明"),
    ("正统", "明"), ("景泰", "明"), ("天顺", "明"), ("成化", "明"), ("弘治", "明"),
    ("正德", "明"), ("嘉靖", "明"), ("隆庆", "明"), ("万历", "明"), ("泰昌", "明"),
    ("天启", "明"), ("崇祯", "明"), ("民国", "民国"),
)


def reign_era(title):
    for reign, era in REIGN_ERA:
        if reign in title:
            return era
    return ""


def publish_rows(rows):
    tang = {
        (row[0], row[6], row[7])
        for row in rows
        if row[9] == "全唐诗"
    }
    kept = []
    for row in rows:
        if len(row[6]) < 4:
            continue
        if row[9] == "全宋诗" and (row[0], row[6], row[7]) in tang:
            continue
        if not row[8]:
            era = reign_era(row[7])
            if era:
                row = row[:8] + (era,) + row[9:]
        kept.append(row)
    return kept


def book_name(filename):
    stem = os.path.splitext(os.path.basename(filename))[0]
    stem = re.sub(r"^\d+-", "", stem)
    return stem


def place_from_title(title):
    title = re.sub(r"^(乾隆|康熙|嘉庆|道光|光绪|嘉靖|正德|天启|顺治|雍正|民国)", "", title)
    match = re.match(r"^(.{2,8}?)(?:县|府|州|厅|卫)?志$", title)
    if not match:
        return ""
    name = match.group(1)
    if name.endswith("通"):
        name = name[:-1]
    return name if len(name) >= 2 else ""


def read_text(path):
    raw = open(path, "rb").read()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def sentences_of(text):
    pieces = re.split(r"[。！？；\n\r]+", text)
    for piece in pieces:
        line = piece.strip().strip("　 \t")
        if 6 <= len(line) <= 160:
            yield line


def add_hits(rows, seen, by_source, index, places, seasons, senses, line, title, era, source, default_place):
    hits = find_words(line, index)
    if not hits:
        return
    found = find_labels(line, places)
    if default_place and default_place not in found:
        found.insert(0, default_place)
    place = "、".join(found[:3])
    season = "、".join(find_labels(line, seasons))
    sense = "、".join(find_labels(line, senses))
    cite = "《%s》" % title
    for simp, category, obj, _start, _end in hits:
        key = (simp, line, "", title, source)
        if key in seen:
            continue
        seen.add(key)
        rows.append((simp, category, obj, place, season, sense, line, cite, era, source))
        by_source[source] += 1


def add_prose(rows, seen, by_source, index, places, seasons, senses):
    folders = [
        (os.path.join(CORPUS, "本草"), "本草", True),
        (os.path.join(CORPUS, "方志"), "方志", False),
    ]
    for folder, source, is_bencao in folders:
        if not os.path.isdir(folder):
            print("SOURCE", source, "files", 0, flush=True)
            continue
        paths = [
            os.path.join(folder, name)
            for name in sorted(os.listdir(folder))
            if name.endswith(".txt")
        ]
        print("SOURCE", source, "files", len(paths), flush=True)
        for path in paths:
            title = book_name(path)
            era = BENCAO_ERA.get(title, "") if is_bencao else reign_era(title)
            default_place = "" if is_bencao else place_from_title(title)
            text = read_text(path)
            before = len(rows)
            for line in sentences_of(text):
                add_hits(
                    rows, seen, by_source, index, places, seasons, senses,
                    line, title, era, source, default_place,
                )
            print("  ", title, "added", len(rows) - before, "total", len(rows), flush=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    index, word_forms = build_index()
    places = build_places()
    seasons = build_seasons()
    senses = build_senses()
    print("lexicon_forms", word_forms, flush=True)
    rows = []
    seen = set()
    by_source = defaultdict(int)
    for folder, source, era, prefix in SOURCES:
        paths = files_for(folder, prefix)
        print("SOURCE", source, "files", len(paths), flush=True)
        for path in paths:
            try:
                works = works_in(path)
            except json.JSONDecodeError:
                print("BAD", path, flush=True)
                continue
            for work in works:
                if not isinstance(work, dict):
                    continue
                author = work.get("author") or ""
                title = title_of(work)
                cite = "%s《%s》" % (author, title) if author or title else ""
                for line in paragraphs_of(work):
                    hits = find_words(line, index)
                    if not hits:
                        continue
                    place = "、".join(find_labels(line, places)[:3])
                    season = "、".join(find_labels(line, seasons))
                    sense = "、".join(find_labels(line, senses))
                    for simp, category, obj, _start, _end in hits:
                        key = (simp, line, author, title, source)
                        if key in seen:
                            continue
                        seen.add(key)
                        rows.append((simp, category, obj, place, season, sense, line, cite, era, source))
                        by_source[source] += 1
            print("  ", os.path.basename(path), "total", len(rows), flush=True)
    add_prose(rows, seen, by_source, index, places, seasons, senses)
    rows = publish_rows(rows)
    by_source = defaultdict(int)
    for row in rows:
        by_source[row[9]] += 1
    with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["气味词", "类别", "对象", "地方", "季节", "感官", "原文", "出处", "时代", "来源"])
        writer.writerows(rows)
    random.seed(7)
    sample = rows if len(rows) <= 1000 else random.sample(rows, 1000)
    with open(SAMPLE_PATH, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["气味词", "类别", "对象", "地方", "季节", "感官", "原文", "出处", "时代", "来源"])
        writer.writerows(sample)
    print("TOTAL", len(rows), flush=True)
    for source, count in sorted(by_source.items(), key=lambda item: -item[1]):
        print("COUNT", source, count, flush=True)
    print("WROTE", CSV_PATH, flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
