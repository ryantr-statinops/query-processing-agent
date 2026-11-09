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


    def test_csv_preserves_codes_and_raw_money(self):
        from datamate.data.sources import csv_source, load_csv

        with TemporaryDirectory() as folder:
            path = Path(folder) / "sales.csv"
            path.write_text('id,amount,other\n001,"12,300",x\n', encoding="utf-8")
            binding, = bind_sources([csv_source(path)], {"id": ("id",), "amount": ("amount",)}, ())
            self.assertEqual(load_csv(binding).row(0), ("001", "12,300"))


    def test_sheet_year(self):
        from datamate.data.sources import sheet_year

        self.assertEqual(sheet_year(Source(Path("sales.xlsx"), "09.2026", ("Ngày",))), 2026)
        self.assertIsNone(sheet_year(Source(Path("sales.xlsx"), "Sheet1", ("Ngày",))))


    def test_sqlite_preserves_source_and_quotes_names(self):
        import sqlite3
        from datamate.data.sources import sqlite_sources, load_sqlite

        with TemporaryDirectory() as folder:
            path = Path(folder) / "pos.sqlite"
            with sqlite3.connect(path) as database:
                database.execute('CREATE TABLE "receipt detail" ("item code" TEXT)')
                database.execute('INSERT INTO "receipt detail" VALUES (?)', ("001",))
            database.close()
            before = path.read_bytes()
            binding, = bind_sources(list(sqlite_sources(path)), {"id": ("item code",)}, ())
            self.assertEqual(load_sqlite(binding).row(0), ("001",))
            self.assertEqual(path.read_bytes(), before)
