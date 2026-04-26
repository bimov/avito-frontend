from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ocr_app.ocr_utils import OCRWord, is_allowed_filename, normalize_sort_option, normalize_threshold, parse_tsv, select_words


SAMPLE_TSV = """level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext
1\t1\t0\t0\t0\t0\t0\t0\t1200\t800\t-1\t
5\t1\t1\t1\t1\t1\t20\t30\t180\t40\t96.2\tМОЛОКО
5\t1\t1\t1\t1\t2\t220\t30\t140\t40\t89.3\tХЛЕБ
5\t1\t1\t1\t1\t3\t380\t30\t160\t40\t74.0\tкасса
"""


class OCRUtilsTests(unittest.TestCase):
    def test_parse_tsv_extracts_word_rows(self) -> None:
        words = parse_tsv(SAMPLE_TSV)

        self.assertEqual(3, len(words))
        self.assertEqual("МОЛОКО", words[0].text)
        self.assertAlmostEqual(0.962, words[0].confidence)
        self.assertEqual([(20, 30), (200, 30), (200, 70), (20, 70)], words[0].polygon)

    def test_select_words_filters_by_threshold_and_sorts_descending(self) -> None:
        words = parse_tsv(SAMPLE_TSV)

        filtered = select_words(words, threshold=0.85, sort_option="confidence-desc")

        self.assertEqual(["МОЛОКО", "ХЛЕБ"], [word.text for word in filtered])

    def test_select_words_can_sort_alphabetically(self) -> None:
        words = [
            OCRWord(text="ЯБЛОКО", confidence=0.90, left=0, top=0, width=10, height=10),
            OCRWord(text="БАНАН", confidence=0.95, left=0, top=0, width=10, height=10),
        ]

        filtered = select_words(words, threshold=0.5, sort_option="word-asc")

        self.assertEqual(["БАНАН", "ЯБЛОКО"], [word.text for word in filtered])

    def test_normalizers_return_safe_defaults(self) -> None:
        self.assertEqual(0.85, normalize_threshold(None))
        self.assertEqual(1.0, normalize_threshold("3"))
        self.assertEqual(0.0, normalize_threshold("-2"))
        self.assertEqual("confidence-desc", normalize_sort_option("unsupported"))

    def test_allowed_file_types_match_supported_extensions(self) -> None:
        self.assertTrue(is_allowed_filename("receipt.jpeg"))
        self.assertTrue(is_allowed_filename("photo.PNG"))
        self.assertFalse(is_allowed_filename("archive.zip"))
        self.assertFalse(is_allowed_filename("noextension"))

    def test_fragment_uses_short_word_piece(self) -> None:
        word = OCRWord(text="МОЛОКО", confidence=0.98, left=0, top=0, width=10, height=10)

        self.assertEqual("МОЛО...", word.fragment)


if __name__ == "__main__":
    unittest.main()
