import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chunking import chunk_units
from app.extraction import ExtractedUnit


class TestChunking(unittest.TestCase):
    def test_short_unit_becomes_single_chunk_and_keeps_source_ref(self):
        units = [ExtractedUnit(text="Texto corto.", source_ref={"page": 3})]
        chunks = chunk_units(units, chunk_size=1200)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].source_ref, {"page": 3})

    def test_long_unit_splits_with_overlap_and_part_index(self):
        text = "A" * 3000
        units = [ExtractedUnit(text=text, source_ref={"page": 1})]
        chunks = chunk_units(units, chunk_size=1000, overlap=100)
        self.assertGreater(len(chunks), 1)
        for i, c in enumerate(chunks):
            self.assertEqual(c.source_ref["page"], 1)
            self.assertEqual(c.source_ref["part"], i)
        # el texto reconstruido (sin traslape) cubre todo el original
        self.assertGreaterEqual(sum(len(c.text) for c in chunks), len(text))

    def test_empty_units_are_skipped(self):
        units = [ExtractedUnit(text="   ", source_ref={"page": 1})]
        chunks = chunk_units(units)
        self.assertEqual(chunks, [])


if __name__ == "__main__":
    unittest.main()
