#!/usr/bin/env python3
"""
scripts/enrich_quran_crossrefs.py
Scans the entire Sunan an-Nasa'i corpus (5,765 hadiths across 51 books) for Quranic verse citations.
Injects canonical cross-references with direct links to the al-quran project:
Template: https://maktabah-maftoohah.github.io/al-quran/{surah}/{ayah}
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HADITHS_DIR = ROOT / "data" / "hadiths"
SURAHS_FILE = ROOT.parent / "al-quran" / "data" / "surahs.json"

if not SURAHS_FILE.exists():
    raise FileNotFoundError(f"Missing canonical Surahs catalogue at {SURAHS_FILE}")

with open(SURAHS_FILE, "r", encoding="utf-8") as f:
    surahs_data = json.load(f)

def normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())

surah_map = {}
for s in surahs_data:
    num = s["number"]
    total_a = s["total_ayahs"]
    lat = s.get("name_latin", "")
    ms = s.get("name_ms", "")
    ar = s.get("name_arabic", "")
    
    surah_map[normalize(lat)] = (num, ms, total_a)
    surah_map[normalize(ms)] = (num, ms, total_a)
    
    # Strip common prefixes
    for prefix in ("al", "an", "at", "as", "ar", "az", "ad", "ash", "asy", "ath", "aal", "alu"):
        n_lat = normalize(lat)
        n_ms = normalize(ms)
        if n_lat.startswith(prefix):
            surah_map[n_lat[len(prefix):]] = (num, ms, total_a)
        if n_ms.startswith(prefix):
            surah_map[n_ms[len(prefix):]] = (num, ms, total_a)

# Common colloquial Indonesian & Malay Quranic spellings
aliases = {
    "baqoroh": 2, "albaqoroh": 2, "al-baqarah": 2, "baqarah": 2,
    "aliimran": 3, "aluimran": 3, "ali-imran": 3, "al-imran": 3,
    "nisa": 4, "an-nisa": 4, "annisa": 4,
    "maidah": 5, "almaidah": 5, "al-maidah": 5,
    "anam": 6, "alanam": 6, "al-anam": 6,
    "araf": 7, "alaraf": 7, "al-araf": 7,
    "anfal": 8, "alanfal": 8, "al-anfal": 8,
    "taubah": 9, "attaubah": 9, "at-taubah": 9, "at-tawbah": 9, "baraah": 9, "baraa": 9,
    "isra": 17, "alisra": 17, "baniisrail": 17,
    "kahfi": 18, "alkahfi": 18, "al-kahfi": 18, "kahf": 18,
    "maryam": 19,
    "taha": 20, "ta-ha": 20,
    "anbiya": 21, "al-anbiya": 21,
    "hajj": 22, "al-hajj": 22,
    "nur": 24, "an-nur": 24,
    "syuara": 26, "asysyuara": 26, "asy-syuara": 26,
    "naml": 27, "annaml": 27, "an-naml": 27,
    "luqman": 31,
    "ahzab": 33, "alahzab": 33, "al-ahzab": 33,
    "saba": 34, "as-saba": 34,
    "fathir": 35,
    "yasin": 36, "ya-sin": 36,
    "shad": 38, "shaad": 38, "shadd": 38,
    "fath": 48, "alfath": 48, "al-fath": 48,
    "hujurat": 49, "al-hujurat": 49,
    "tur": 52, "ath-thur": 52, "attur": 52,
    "najm": 53, "an-najm": 53, "annajm": 53,
    "hasyr": 59, "alhasyr": 59, "al-hashr": 59,
    "mumtahanah": 60, "al-mumtahanah": 60,
    "jumuah": 62, "aljumuah": 62, "al-jumuah": 62,
    "munafiqun": 63, "almunafiqun": 63, "almunafiqin": 63,
    "talaq": 65, "at-talaq": 65,
    "tahrim": 66, "at-tahrim": 66, "attahrim": 66,
    "mulk": 67, "al-mulk": 67,
    "qiyamah": 75, "al-qiyamah": 75, "alqiyama": 75,
    "mursalat": 77, "al-mursalat": 77, "walmursalat": 77,
    "naba": 78, "an-naba": 78,
    "insyiqaq": 84, "alinsyiqaq": 84, "al-insyiqaq": 84,
    "ala": 87, "al-ala": 87, "alala": 87,
    "ghaasyiyah": 88, "alghaasyiyah": 88, "ghasyiyah": 88,
    "fajr": 89, "al-fajr": 89,
    "balad": 90, "al-balad": 90,
    "syams": 91, "asy-syams": 91,
    "layl": 92, "al-layl": 92,
    "adhdhuha": 93, "ad-dhuha": 93, "dhuha": 93,
    "insyirah": 94, "al-insyirah": 94, "syarh": 94,
    "tin": 95, "at-tin": 95,
    "alaq": 96, "al-alaq": 96, "alalaq": 96,
    "qadr": 97, "al-qadr": 97,
    "zalzalah": 99, "az-zalzalah": 99,
    "adiyat": 100, "al-adiyat": 100,
    "qariah": 101, "al-qariah": 101,
    "takatsur": 102, "at-takatsur": 102,
    "asr": 103, "al-asr": 103,
    "fil": 105, "al-fil": 105,
    "quraisy": 106,
    "kautsar": 108, "al-kautsar": 108,
    "kafirun": 109, "al-kafirun": 109,
    "nasr": 110, "an-nasr": 110,
    "masad": 111, "al-masad": 111, "lahab": 111,
    "ikhlas": 112, "al-ikhlas": 112,
    "falaq": 113, "al-falaq": 113,
    "nas": 114, "an-nas": 114
}

for k, v in aliases.items():
    s_obj = surahs_data[v - 1]
    surah_map[normalize(k)] = (v, s_obj.get("name_ms"), s_obj["total_ayahs"])

def extract_quran_citations(h: dict) -> list[dict]:
    en = h.get("translations", {}).get("en", "")
    ms = h.get("translations", {}).get("ms", "")
    
    found_refs = []
    
    # 1. English format: (V. s:a), (s:a), (s.a)
    for s, a in re.findall(r"\((?:[Vv]\.?\s*)?(\d{1,3})[:.](\d{1,3})\)", en):
        s_i, a_i = int(s), int(a)
        if 1 <= s_i <= 114:
            s_obj = surahs_data[s_i - 1]
            max_a = s_obj["total_ayahs"]
            if 1 <= a_i <= max_a:
                s_name = s_obj.get("name_ms", f"Surah {s_i}")
                found_refs.append({
                    "type": "quran",
                    "surah": s_i,
                    "ayah": a_i,
                    "surah_name": s_name,
                    "url": f"https://maktabah-maftoohah.github.io/al-quran/{s_i}/{a_i}"
                })
            
    # 2. Indonesian/Malay format (QS. Name: Ayah), (As. Name: Ayah), (Surat Name: Ayah)
    for m in re.finditer(r"(?:\(QS\.?|QS\.?|\bsurat\b|\bsurah\b|\bAs\.)\s*([A-Za-z\'-]+(?:\s+[A-Za-z\'-]+)?)\s*(?:[:,\.]|\bayat\b)\s*(\d{1,3})", ms, re.IGNORECASE):
        raw_name = m.group(1).strip()
        raw_ay = m.group(2)
        n_name = normalize(raw_name)
        if n_name in surah_map:
            s_id, s_name, max_a = surah_map[n_name]
            a_id = int(raw_ay) if raw_ay else 1
            if a_id > max_a:
                a_id = max_a
            found_refs.append({
                "type": "quran",
                "surah": s_id,
                "ayah": a_id,
                "surah_name": s_name,
                "url": f"https://maktabah-maftoohah.github.io/al-quran/{s_id}/{a_id}"
            })

    # 3. Indonesian/Malay format (QS. Name) without specific ayah (default to Ayah 1)
    for m in re.finditer(r"\(QS\.?\s*([A-Za-z\'-]+(?:\s+[A-Za-z\'-]+)?)\)", ms, re.IGNORECASE):
        raw_name = m.group(1).strip()
        n_name = normalize(raw_name)
        if n_name in surah_map:
            s_id, s_name, max_a = surah_map[n_name]
            found_refs.append({
                "type": "quran",
                "surah": s_id,
                "ayah": 1,
                "surah_name": s_name,
                "url": f"https://maktabah-maftoohah.github.io/al-quran/{s_id}/1"
            })

    # Deduplicate by (surah, ayah)
    unique = []
    seen = set()
    for r in found_refs:
        key = (r["surah"], r["ayah"])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique

def main():
    total_hadiths_linked = 0
    total_citations = 0
    updated_files = 0

    print("=== Scanning Sunan an-Nasa'i corpus for Quranic verse citations ===")

    for hf in sorted(HADITHS_DIR.glob("*.json")):
        with open(hf, "r", encoding="utf-8") as f:
            hadiths = json.load(f)

        file_modified = False
        for h in hadiths:
            quran_refs = extract_quran_citations(h)
            if quran_refs:
                # Merge existing non-quran cross-references if any
                existing = [cr for cr in h.get("cross_references", []) if cr.get("type") != "quran"]
                h["cross_references"] = existing + quran_refs
                total_hadiths_linked += 1
                total_citations += len(quran_refs)
                file_modified = True

        if file_modified:
            with open(hf, "w", encoding="utf-8") as f:
                json.dump(hadiths, f, ensure_ascii=False, indent=2)
            updated_files += 1

    print(f"Successfully processed {updated_files} book files.")
    print(f"Total Hadiths enriched with Quran cross-references: {total_hadiths_linked}")
    print(f"Total Quranic verse links created: {total_citations}")

if __name__ == "__main__":
    main()
