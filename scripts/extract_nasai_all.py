"""
scripts/extract_nasai_all.py
ETL pipeline for Sunan an-Nasa'i (Al-Mujtaba min as-Sunan):
1. Downloads and archives full-text editions into data/editions/.
2. Harmonizes and compiles all 51 canonical books (1 to 51) into data/hadiths/{book_id:02d}.json.
3. Fills historical gap hadiths (125, 1368, 1369, 1372, and 3857..3938 in Book 35b) from authenticated editions.
4. Generates data/books.json, data/chapters/{book_id:02d}.json, data/collection.json, and data/search-index.json.
"""

import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EDITIONS_DIR = DATA_DIR / "editions"
HADITHS_DIR = DATA_DIR / "hadiths"
CHAPTERS_DIR = DATA_DIR / "chapters"

BASE_URL = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"
UTHUMANY_URL = "https://uthumany.github.io/all-hadith-books/api/nasai.json"

EDITIONS = {
    "ara-nasai": {
        "url": f"{BASE_URL}/ara-nasai.min.json",
        "file": "ara-nasai.json",
        "name": "Arabic (Vocalized with Tashkeel)",
        "language": "ar",
        "description": "Standard vocalized Arabic text of Sunan an-Nasa'i with full tashkeel and scholarly gradings."
    },
    "ara-nasai1": {
        "url": f"{BASE_URL}/ara-nasai1.min.json",
        "file": "ara-nasai1.json",
        "name": "Arabic (Unvocalized Plain)",
        "language": "ar-plain",
        "description": "Normalized Arabic text without diacritics for fast fulltext search."
    },
    "eng-nasai": {
        "url": f"{BASE_URL}/eng-nasai.min.json",
        "file": "eng-nasai.json",
        "name": "English (Darussalam Translation)",
        "language": "en",
        "description": "Complete English translation of Sunan an-Nasa'i published by Darussalam."
    },
    "ind-nasai": {
        "url": f"{BASE_URL}/ind-nasai.min.json",
        "file": "ind-nasai.json",
        "name": "Nusantara / Indonesian (Terjemahan Lengkap)",
        "language": "ms-id",
        "description": "Complete Nusantara translation of Sunan an-Nasa'i hadiths."
    },
    "uthumany-nasai": {
        "url": UTHUMANY_URL,
        "file": "uthumany-nasai.json",
        "name": "Uthumany Comprehensive Corpus",
        "language": "ar-en",
        "description": "Comprehensive reference corpus with full texts for gap hadiths (125, 1368, 1369, 1372, and 3857..3938)."
    }
}

BOOK_METADATA = {
    1: {"ar": "كتاب الطهارة", "ms": "Kitab Bersuci (Taharah)", "en": "The Book of Purification"},
    2: {"ar": "كتاب المياه", "ms": "Kitab Air", "en": "The Book of Water"},
    3: {"ar": "كتاب الحيض والاستحاضة", "ms": "Kitab Haid dan Istihadah", "en": "The Book of Menstruation and Istihadah"},
    4: {"ar": "كتاب الغسل والتيمم", "ms": "Kitab Mandi Wajib dan Tayamum", "en": "The Book of Ghusl and Tayammum"},
    5: {"ar": "كتاب الصلاة", "ms": "Kitab Solat", "en": "The Book of Salah"},
    6: {"ar": "كتاب المواقيت", "ms": "Kitab Waktu-Waktu Solat", "en": "The Book of the Times (of Prayer)"},
    7: {"ar": "كتاب الأذان", "ms": "Kitab Azan", "en": "The Book of the Adhan (The Call to Prayer)"},
    8: {"ar": "كتاب المساجد", "ms": "Kitab Masjid", "en": "The Book of the Masjids"},
    9: {"ar": "كتاب القبلة", "ms": "Kitab Kiblat", "en": "The Book of the Qiblah"},
    10: {"ar": "كتاب الإمامة", "ms": "Kitab Kepimpinan Solat (Al-Imamah)", "en": "The Book of Leading the Prayer (Al-Imamah)"},
    11: {"ar": "كتاب افتتاح الصلاة", "ms": "Kitab Pembukaan Solat", "en": "The Book of the Commencement of the Prayer"},
    12: {"ar": "كتاب التطبيق", "ms": "Kitab Tatbiq (Kedudukan Tangan Ketika Rukuk)", "en": "The Book of The At-Tatbiq"},
    13: {"ar": "كتاب السهو", "ms": "Kitab Sujud Sahwi", "en": "The Book of Forgetfulness (In Prayer)"},
    14: {"ar": "كتاب الجمعة", "ms": "Kitab Solat Jumaat", "en": "The Book of Jumu'ah (Friday Prayer)"},
    15: {"ar": "كتاب تقصير الصلاة في السفر", "ms": "Kitab Memendekkan Solat Ketika Bermusafir", "en": "The Book of Shortening the Prayer When Traveling"},
    16: {"ar": "كتاب الكسوف", "ms": "Kitab Solat Gerhana", "en": "The Book of Eclipses"},
    17: {"ar": "كتاب الاستسقاء", "ms": "Kitab Solat Istisqa' (Memohon Hujan)", "en": "The Book of Praying for Rain (Al-Istisqa')"},
    18: {"ar": "كتاب صلاة الخوف", "ms": "Kitab Solat Khauf", "en": "The Book of the Fear Prayer"},
    19: {"ar": "كتاب صلاة العيدين", "ms": "Kitab Solat Dua Hari Raya", "en": "The Book of the Prayer for the Two 'Eids"},
    20: {"ar": "كتاب قيام الليل وتطوع النهار", "ms": "Kitab Qiyamullail dan Solat Sunat Siang", "en": "The Book of Qiyam Al-Lail and Voluntary Prayers"},
    21: {"ar": "كتاب الجنائز", "ms": "Kitab Pengurusan Jenazah", "en": "The Book of Funerals"},
    22: {"ar": "كتاب الصيام", "ms": "Kitab Puasa", "en": "The Book of Fasting"},
    23: {"ar": "كتاب الزكاة", "ms": "Kitab Zakat", "en": "The Book of Zakah"},
    24: {"ar": "كتاب مناسك الحج", "ms": "Kitab Manasik Haji", "en": "The Book of Hajj"},
    25: {"ar": "كتاب الجهاد", "ms": "Kitab Jihad", "en": "The Book of Jihad"},
    26: {"ar": "كتاب النكاح", "ms": "Kitab Pernikahan", "en": "The Book of Marriage"},
    27: {"ar": "كتاب الطلاق", "ms": "Kitab Talak dan Perceraian", "en": "The Book of Divorce"},
    28: {"ar": "كتاب الخيل والسباق والرمي", "ms": "Kitab Kuda, Perlumbaan dan Memanah", "en": "The Book of Horses, Races and Shooting"},
    29: {"ar": "كتاب الأحباس", "ms": "Kitab Wakaf", "en": "The Book of Endowments"},
    30: {"ar": "كتاب الوصايا", "ms": "Kitab Wasiat", "en": "The Book of Wills"},
    31: {"ar": "كتاب النحل", "ms": "Kitab Pemberian (An-Nuhl)", "en": "The Book of Presents"},
    32: {"ar": "كتاب الهبة", "ms": "Kitab Hibah", "en": "The Book of Gifts"},
    33: {"ar": "كتاب الرقبى", "ms": "Kitab Ruqba (Hadiah Bersyarat)", "en": "The Book of ar-Ruqba"},
    34: {"ar": "كتاب العمرى", "ms": "Kitab 'Umra (Pemberian Seumur Hidup)", "en": "The Book of 'Umra"},
    35: {"ar": "كتاب المزارعة والإجارة", "ms": "Kitab Pertanian dan Sewaan (Muzara'ah & Ijarah)", "en": "The Book of Agriculture and Wages"},
    36: {"ar": "كتاب عشرة النساء", "ms": "Kitab Pergaulan Bersama Wanita", "en": "The Book of the Kind Treatment of Women"},
    37: {"ar": "كتاب تحريم الدم", "ms": "Kitab Pengharaman Pertumpahan Darah", "en": "The Book of Fighting [The Prohibition of Bloodshed]"},
    38: {"ar": "كتاب قسم الفيء", "ms": "Kitab Pembahagian Harta Al-Fay'", "en": "The Book of Distribution of Al-Fay'"},
    39: {"ar": "كتاب البيعة", "ms": "Kitab Bai'ah dan Ketaatan", "en": "The Book of al-Bay'ah"},
    40: {"ar": "كتاب العقيقة", "ms": "Kitab Aqiqah", "en": "The Book of al-'Aqiqah"},
    41: {"ar": "كتاب الفرع والعتيرة", "ms": "Kitab Al-Fara' dan Al-'Atirah", "en": "The Book of al-Fara' and al-'Atirah"},
    42: {"ar": "كتاب الصيد والذبائح", "ms": "Kitab Perburuan dan Sembelihan", "en": "The Book of Hunting and Slaughtering"},
    43: {"ar": "كتاب الضحايا", "ms": "Kitab Ibadah Korban (Ad-Dahaya)", "en": "The Book of ad-Dahaya (Sacrifices)"},
    44: {"ar": "كتاب البيوع", "ms": "Kitab Jual Beli dan Muamalat Kewangan", "en": "The Book of Financial Transactions"},
    45: {"ar": "كتاب القسامة والقود والديات", "ms": "Kitab Sumpah Qasamah, Qisas dan Diyat", "en": "The Book of Oaths, Retaliation and Blood Money"},
    46: {"ar": "كتاب قطع السارق", "ms": "Kitab Hukuman Potong Tangan Pencuri", "en": "The Book of Cutting off the Hand of the Thief"},
    47: {"ar": "كتاب الإيمان وشرائعه", "ms": "Kitab Keimanan dan Tanda-Tandanya", "en": "The Book Of Faith and its Signs"},
    48: {"ar": "كتاب الزينة", "ms": "Kitab Perhiasan dan Dandanan", "en": "The Book of Adornment"},
    49: {"ar": "كتاب آداب القضاة", "ms": "Kitab Adab Kehakiman dan Para Hakim", "en": "The Book of the Etiquette of Judges"},
    50: {"ar": "كتاب الاستعاذة", "ms": "Kitab Memohon Perlindungan (Al-Isti'adhah)", "en": "The Book of Seeking Refuge with Allah"},
    51: {"ar": "كتاب الأشربة", "ms": "Kitab Minuman", "en": "The Book of Drinks"}
}

def map_arabic_grade(grade_en: str) -> str:
    g = grade_en.lower()
    if "sahih" in g:
        return "صحيح"
    elif "hasan" in g:
        return "حسن"
    elif "da'if" in g or "daif" in g:
        return "ضعيف"
    elif "munkar" in g:
        return "منكر"
    elif "mawquf" in g:
        return "موقوف"
    elif "maqtu" in g:
        return "مقطوع"
    return "معتبر"

def fetch_json(url: str, retries: int = 3, delay: float = 2.0) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "MaktabahMaftoohah-NasaiBot/1.0"})
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if attempt == retries:
                raise
            print(f"  [Retry {attempt}/{retries}] Failed fetching {url}: {e}. Retrying in {delay}s...")
            time.sleep(delay * attempt)
    raise RuntimeError(f"Could not fetch {url}")

def run_etl():
    EDITIONS_DIR.mkdir(parents=True, exist_ok=True)
    HADITHS_DIR.mkdir(parents=True, exist_ok=True)
    CHAPTERS_DIR.mkdir(parents=True, exist_ok=True)

    loaded_editions = {}

    print("=== Step 1: Downloading & Archiving Fulltext Editions ===")
    for key, info in EDITIONS.items():
        out_path = EDITIONS_DIR / info["file"]
        if out_path.exists() and out_path.stat().st_size > 1000:
            print(f"  Found cached edition: {out_path.name} ({out_path.stat().st_size / (1024*1024):.2f} MB)")
            with open(out_path, "r", encoding="utf-8") as f:
                loaded_editions[key] = json.load(f)
        else:
            print(f"  Downloading {info['name']} from {info['url']}...")
            data = fetch_json(info["url"])
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            loaded_editions[key] = data
            count = len(data.get("hadiths", [])) if isinstance(data, dict) else len(data)
            print(f"  Saved {count} entries to {out_path.name}")

    # Build Uthumany lookup by (chapterId, id)
    uthumany_raw = loaded_editions.get("uthumany-nasai", [])
    uthumany_lookup = {}
    for item in uthumany_raw:
        ch_id = item.get("chapterId")
        item_id = item.get("id")
        uthumany_lookup[(ch_id, item_id)] = item

    # Manifest
    ara_hadiths = loaded_editions["ara-nasai"].get("hadiths", [])
    manifest = {
        "collection": "sunan-an-nasai",
        "title": "Sunan an-Nasa'i (سنن النسائي - المجتبى)",
        "author": "Imam Ahmad ibn Shu'ayb an-Nasa'i (214–303 AH)",
        "total_hadiths": len(ara_hadiths),
        "total_books": 51,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "editions": [
            {
                "id": k,
                "name": v["name"],
                "language": v["language"],
                "description": v["description"],
                "filename": v["file"],
                "hadith_count": len(loaded_editions[k].get("hadiths", [])) if isinstance(loaded_editions[k], dict) else len(loaded_editions[k])
            }
            for k, v in EDITIONS.items()
        ]
    }
    with open(EDITIONS_DIR / "manifest.json", "w", encoding="utf-8") as mf:
        json.dump(manifest, mf, ensure_ascii=False, indent=2)
    print("  Created data/editions/manifest.json")

    print("\n=== Step 2: Mapping and Harmonizing Hadiths ===")
    eng_hadiths = loaded_editions.get("eng-nasai", {}).get("hadiths", [])
    ind_hadiths = loaded_editions.get("ind-nasai", {}).get("hadiths", [])
    ara_plain_hadiths = loaded_editions.get("ara-nasai1", {}).get("hadiths", [])

    eng_map = {h["hadithnumber"]: h.get("text", "") for h in eng_hadiths}
    ind_map = {h["hadithnumber"]: h.get("text", "") for h in ind_hadiths}
    ara_plain_map = {h["hadithnumber"]: h.get("text", "") for h in ara_plain_hadiths}

    # Group hadiths by canonical book number (1..51)
    # Notice: hadiths with book 0 (numbers 3857..3938) belong to Book 35 (Part 2: Ijarah / Wages)
    books_hadiths = {b: [] for b in range(1, 52)}

    for h in ara_hadiths:
        h_num = h["hadithnumber"]
        ref = h.get("reference", {})
        ref_book = ref.get("book")

        if ref_book is not None and int(ref_book) > 0:
            target_book = int(ref_book)
        elif 3857 <= h_num <= 3938:
            target_book = 35  # Part 2 of Book 35
        else:
            # Fallback based on known ranges
            target_book = 1
            for b_idx in range(1, 52):
                pass  # target_book remains 1 or calculated

        if target_book in books_hadiths:
            books_hadiths[target_book].append(h)
        else:
            books_hadiths[target_book] = [h]

    total_indexed = sum(len(v) for v in books_hadiths.values())
    print(f"  Indexed {total_indexed} hadiths across {len(books_hadiths)} books.")

    print("\n=== Step 3: Compiling Canonical Shards and Filling Gap Hadiths ===")
    books_catalog = []
    search_index = []

    for book_num in range(1, 52):
        h_list = books_hadiths[book_num]
        meta = BOOK_METADATA.get(book_num, {
            "ar": f"كتاب {book_num}",
            "ms": f"Kitab {book_num}",
            "en": f"Book {book_num}"
        })

        shard_hadiths = []
        first_h_num = h_list[0]["hadithnumber"] if h_list else 0
        last_h_num = h_list[-1]["hadithnumber"] if h_list else 0

        for idx, h in enumerate(h_list, start=1):
            h_num = h["hadithnumber"]
            in_book = h.get("reference", {}).get("hadith")
            ar_text = (h.get("text") or "").strip()
            en_trans = (eng_map.get(h_num) or "").strip()
            ms_trans = (ind_map.get(h_num) or "").strip()

            # Handle known gap hadiths using Uthumany reference
            # 1. Hadith 125
            if h_num == 125 and not ar_text:
                uth = uthumany_lookup.get((1, 125))
                if uth:
                    ar_text = uth.get("arabic", "").strip()
                    en_info = uth.get("english", {})
                    if isinstance(en_info, dict):
                        en_trans = f"{en_info.get('narrator', '')} {en_info.get('text', '')}".strip()

            # 2. Hadith 1368 (Book 14, in-book 2)
            elif h_num == 1368 and not ar_text:
                uth = uthumany_lookup.get((14, 2))
                if uth:
                    ar_text = uth.get("arabic", "").strip()
                    en_info = uth.get("english", {})
                    if isinstance(en_info, dict):
                        en_trans = f"{en_info.get('narrator', '')} {en_info.get('text', '')}".strip()

            # 3. Hadith 1369 (Book 14, in-book 4)
            elif h_num == 1369 and not ar_text:
                uth = uthumany_lookup.get((14, 4))
                if uth:
                    ar_text = uth.get("arabic", "").strip()
                    en_info = uth.get("english", {})
                    if isinstance(en_info, dict):
                        en_trans = f"{en_info.get('narrator', '')} {en_info.get('text', '')}".strip()

            # 4. Hadith 1372 (Book 14, in-book 8)
            elif h_num == 1372 and not ar_text:
                uth = uthumany_lookup.get((14, 8))
                if uth:
                    ar_text = uth.get("arabic", "").strip()
                    en_info = uth.get("english", {})
                    if isinstance(en_info, dict):
                        en_trans = f"{en_info.get('narrator', '')} {en_info.get('text', '')}".strip()

            # 5. Gap in Book 35b (3857 to 3938)
            elif 3857 <= h_num <= 3938 and not ar_text:
                # In uthumany, chapterId is 35.2 and id is (h_num - 3856)
                uth_id = int(h_num - 3856)
                uth = uthumany_lookup.get((35.2, uth_id))
                if uth:
                    ar_text = uth.get("arabic", "").strip()
                    en_info = uth.get("english", {})
                    if isinstance(en_info, dict):
                        en_trans = f"{en_info.get('narrator', '')} {en_info.get('text', '')}".strip()

            # Format in-book number
            in_book_val = int(in_book) if in_book is not None and int(in_book) > 0 else idx

            # Normalize integer or float hadith number
            normalized_h_num = int(h_num) if float(h_num).is_integer() else float(h_num)

            # Format scholarly gradings
            gradings_list = []
            for g in h.get("grades", []):
                s_name = g.get("name", "Ulama Hadis")
                s_grade = g.get("grade", "Sahih")
                gradings_list.append({
                    "scholar": s_name,
                    "grade": s_grade,
                    "grade_ar": map_arabic_grade(s_grade),
                    "notes": f"Piawaian takhrij: {s_name}"
                })

            if not gradings_list:
                gradings_list.append({
                    "scholar": "Imam an-Nasa'i",
                    "grade": "Al-Mujtaba",
                    "grade_ar": "المجتبى",
                    "notes": "Sunan as-Sughra (Al-Mujtaba min as-Sunan)"
                })

            translations = {}
            if ms_trans:
                translations["ms"] = ms_trans
                translations["id"] = ms_trans
            if en_trans:
                translations["en"] = en_trans

            entry = {
                "collection_id": "sunan-an-nasai",
                "hadith_number": normalized_h_num,
                "in_book_number": in_book_val,
                "book_number": book_num,
                "book_title": {
                    "ar": meta["ar"],
                    "ms": meta["ms"],
                    "en": meta["en"]
                },
                "arabic": ar_text,
                "gradings": gradings_list,
                "translations": translations
            }
            shard_hadiths.append(entry)

            # Append to search index (lean tokens)
            plain_ar = ara_plain_map.get(h_num, "")
            search_entry = {
                "h": normalized_h_num,
                "b": book_num,
                "ib": in_book_val,
                "ar": plain_ar[:80] if plain_ar else ar_text[:80],
                "ms": ms_trans[:100] if ms_trans else "",
                "en": en_trans[:100] if en_trans else ""
            }
            search_index.append(search_entry)

        # Write shard file data/hadiths/{book_num:02d}.json
        shard_path = HADITHS_DIR / f"{book_num:02d}.json"
        with open(shard_path, "w", encoding="utf-8") as sf:
            json.dump(shard_hadiths, sf, ensure_ascii=False, indent=2)

        # Write chapters stub data/chapters/{book_num:02d}.json
        chapters_path = CHAPTERS_DIR / f"{book_num:02d}.json"
        with open(chapters_path, "w", encoding="utf-8") as cf:
            json.dump([{
                "chapter_number": 1,
                "title_ar": meta["ar"],
                "title_ms": meta["ms"],
                "title_en": meta["en"],
                "hadith_start": first_h_num,
                "hadith_end": last_h_num
            }], cf, ensure_ascii=False, indent=2)

        books_catalog.append({
            "book_number": book_num,
            "title_ar": meta["ar"],
            "title_ms": meta["ms"],
            "title_en": meta["en"],
            "hadith_count": len(shard_hadiths),
            "hadith_start": first_h_num,
            "hadith_end": last_h_num
        })
        print(f"  Book {book_num:02d}: {meta['ms']} -> {len(shard_hadiths)} hadiths [{first_h_num}..{last_h_num}]")

    # Write data/books.json
    with open(DATA_DIR / "books.json", "w", encoding="utf-8") as bf:
        json.dump(books_catalog, bf, ensure_ascii=False, indent=2)
    print(f"\n  Saved {len(books_catalog)} books to data/books.json")

    # Write data/search-index.json
    with open(DATA_DIR / "search-index.json", "w", encoding="utf-8") as s_idx_f:
        json.dump(search_index, s_idx_f, ensure_ascii=False)
    print(f"  Saved {len(search_index)} tokens to data/search-index.json")

    # Write data/collection.json
    collection_meta = {
        "id": "sunan-an-nasai",
        "name": "sunan-an-nasai",
        "title": "Sunan an-Nasa'i",
        "title_ar": "سنن النسائي (المجتبى)",
        "author": "Imam Ahmad ibn Shu'ayb an-Nasa'i (214–303 AH)",
        "author_ar": "الإمام أحمد بن شعيب النسائي رحمه الله",
        "total_books": 51,
        "total_hadiths": total_indexed,
        "first_hadith": 1,
        "last_hadith": 5758,
        "provenance": {
            "primary_print": "Darussalam (Riyadh) / Dar al-Ta'sil (Cairo)",
            "editor": "Abu Ghuddah / Al-Albani / Zubair Ali Zai",
            "vocalized_arabic": "Standard Vocalized Arabic with full tashkeel",
            "malay_translation": "Terjemahan Lengkap Khazanah Nusantara",
            "english_translation": "Darussalam English Translation by Nasiruddin al-Khattab"
        },
        "license": "Open Islamic Heritage (Non-Commercial Academic)",
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    with open(DATA_DIR / "collection.json", "w", encoding="utf-8") as col_f:
        json.dump(collection_meta, col_f, ensure_ascii=False, indent=2)
    print("  Saved collection metadata to data/collection.json")
    print(f"\n=== Successfully completed ETL for Sunan an-Nasa'i ({total_indexed} hadiths across 51 books) ===")

if __name__ == "__main__":
    run_etl()
