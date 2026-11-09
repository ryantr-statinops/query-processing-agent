from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from datamate.data.sources import AmbiguousSource, Source, bind_sources


class SourceTests(unittest.TestCase):
    def test_aliases_and_ambiguous_tables(self):
        first = Source(Path("receipts.xlsx"), "Sheet1", ("Thời gian", "Số tiền"))
        other = Source(Path("other.xlsx"), "Sheet1", first.columns)
        fields = {"day": ("thoi_gian",), "amount": ("so_tien",)}
        self.assertEqual(bind_sources([first, other], fields, ("receipts",))[0].fields["day"], "Thời gian")
        self.assertEqual(bind_sources([first], {"missing": ("x",)}, ()), [])
        with self.assertRaises(AmbiguousSource):
            bind_sources([first, other], fields, ())
