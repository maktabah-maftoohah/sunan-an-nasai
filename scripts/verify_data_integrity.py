import json
import os
from pathlib import Path

def test_data_integrity():
    root = Path(__file__).resolve().parent.parent
    hadiths_dir = root / "data" / "hadiths"

    assert hadiths_dir.exists(), "data/hadiths/ directory missing"

    total_hadiths = 0
    book_files = sorted(hadiths_dir.glob("*.json"))
    assert len(book_files) == 51, f"Expected 51 book files, found {len(book_files)}"

    for bf in book_files:
        with open(bf, "rb") as raw_f:
            bom_check = raw_f.read(3)
            assert bom_check != b"\xef\xbb\xbf", f"UTF-8 BOM detected in {bf.name}"

        with open(bf, "r", encoding="utf-8") as f:
            hadiths = json.load(f)

        assert len(hadiths) > 0, f"Empty book file: {bf.name}"

        for h in hadiths:
            total_hadiths += 1
            assert h.get("collection_id") == "sunan-an-nasai", f"Invalid collection_id in {h}"
            assert "hadith_number" in h, f"Missing hadith_number in {h}"
            assert "book_number" in h, f"Missing book_number in {h}"
            assert 1 <= h["book_number"] <= 51, f"Book number out of bounds: {h['book_number']}"
            assert "arabic" in h and len(h["arabic"].strip()) > 0, f"Empty arabic text in Hadith #{h.get('hadith_number')}"
            assert "book_title" in h and "ar" in h["book_title"] and "ms" in h["book_title"], f"Incomplete book_title in {h}"
            assert "gradings" in h and len(h["gradings"]) > 0, f"Missing gradings in Hadith #{h.get('hadith_number')}"
            assert "translations" in h, f"Missing translations in Hadith #{h.get('hadith_number')}"

    assert total_hadiths == 5765, f"Expected 5765 hadiths in total, found {total_hadiths}"

    # Verify books.json
    books_file = root / "data" / "books.json"
    with open(books_file, "r", encoding="utf-8") as f:
        books = json.load(f)
    assert len(books) == 51, f"Expected 51 books in books.json, found {len(books)}"
    assert sum(b["hadith_count"] for b in books) == 5765, "Total book hadith_count sum mismatch"

    # Verify search-index.json
    s_idx = root / "data" / "search-index.json"
    with open(s_idx, "r", encoding="utf-8") as f:
        tokens = json.load(f)
    assert len(tokens) == 5765, f"Expected 5765 tokens in search-index.json, found {len(tokens)}"

    print(f"Data integrity verification PASSED! All 5,765 hadiths across 51 books verified strictly conforming to Maktabah Maftoohah schema.")

if __name__ == "__main__":
    test_data_integrity()
