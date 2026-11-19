"""Tests for the news-image-20261119 v2 entry (main.py).

TDD: these tests were written BEFORE main.py existed.
Run:  python3 -m unittest test_draw -v
"""
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main  # noqa: E402


class TestPngOutput(unittest.TestCase):
    def test_png_bytes_valid(self):
        data = main.render_png()
        self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"), "PNG magic missing")
        # IHDR: length 13, type IHDR, width, height, bitdepth 8, colortype 2
        (length,) = struct.unpack(">I", data[8:12])
        self.assertEqual(data[12:16], b"IHDR")
        self.assertEqual(length, 13)
        width, height, depth, ctype = struct.unpack(">IIBB", data[16:26])
        self.assertEqual((width, height), (1024, 1024))
        self.assertEqual(depth, 8)
        self.assertEqual(ctype, 2)
        self.assertEqual(data[-8:-4], b"IEND", "PNG must end with IEND chunk")
        # every chunk CRC must verify
        pos = 8
        while pos < len(data):
            (ln,) = struct.unpack(">I", data[pos:pos + 4])
            ctype = data[pos + 4:pos + 8]
            body = data[pos + 8:pos + 8 + ln]
            (crc,) = struct.unpack(">I", data[pos + 8 + ln:pos + 12 + ln])
            self.assertEqual(crc, zlib.crc32(ctype + body) & 0xFFFFFFFF,
                             "chunk %r CRC mismatch" % ctype)
            pos += 12 + ln
        self.assertEqual(pos, len(data), "trailing bytes after IEND")

    def test_png_size_under_limit(self):
        data = main.render_png()
        self.assertLessEqual(len(data), 1048576, "image over 1 MiB gate limit")

    def test_deterministic(self):
        self.assertEqual(main.render_png(), main.render_png(),
                         "two renders must be byte-identical (grader runs twice)")

    def test_image_is_not_blank(self):
        data = main.render_png()
        # raw scanlines: filter byte + 1024*3 bytes per row
        idx = data.index(b"IDAT")
        (ln,) = struct.unpack(">I", data[idx - 4:idx])
        raw = zlib.decompress(data[idx + 4:idx + 4 + ln])
        self.assertEqual(len(raw), 1024 * (1 + 1024 * 3))
        pixels = set()
        for y in range(0, 1024, 7):
            row = raw[y * 3073 + 1:(y + 1) * 3073]
            for x in range(0, 3072, 21):
                pixels.add(row[x:x + 3])
        self.assertGreater(len(pixels), 20, "image looks blank / too few colours")


class TestFontAndText(unittest.TestCase):
    def test_font_covers_all_text(self):
        texts = [main.MASTHEAD, main.DATE_LINE, main.FOOTER]
        for s in main.STORIES:
            texts += [s["kicker"], s["headline"], s["summary"]]
        for s in main.STRIP:
            texts += [s["headline"], s["summary"]]
        missing = sorted({ch for t in texts for ch in t if ch not in main.FONT})
        self.assertEqual(missing, [], "glyphs missing for chars: %r" % missing)

    def test_text_width(self):
        # 5px glyph + 1px gap, scaled; no trailing gap after last char:
        # "AB" at scale 2 -> 2*6*2 - 2 = 22; "A" at scale 1 -> 5
        self.assertEqual(main.text_width("AB", 2), 22)
        self.assertEqual(main.text_width("A", 1), 5)
        self.assertEqual(main.text_width("", 3), 0)

    def test_wrap_lines_fit(self):
        for s in main.STORIES:
            for line in main.wrap_text(s["summary"], main.ROW_TEXT_W, 2):
                self.assertLessEqual(main.text_width(line, 2), main.ROW_TEXT_W,
                                     "summary line too wide: %r" % line)
            for line in main.wrap_text(s["headline"], main.ROW_TEXT_W, 3):
                self.assertLessEqual(main.text_width(line, 3), main.ROW_TEXT_W,
                                     "headline line too wide: %r" % line)
        for line in main.wrap_text(main.LEAD["sub"], main.LEAD_TEXT_W, 2):
            self.assertLessEqual(main.text_width(line, 2), main.LEAD_TEXT_W)

    def test_wrap_splits_long_word(self):
        lines = main.wrap_text("AAAAAAAAAAAA", 30, 2)
        for line in lines:
            self.assertLessEqual(main.text_width(line, 2), 30)


class TestCanvasBounds(unittest.TestCase):
    def test_no_out_of_bounds_drawing(self):
        canvas = main.Canvas(1024, 1024)
        main.draw_front_page(canvas)
        self.assertEqual(canvas.oob, 0, "drawing outside the canvas")

    def test_gradient_endpoints(self):
        self.assertEqual(main.lerp_color((0, 0, 0), (255, 255, 255), 0.0), (0, 0, 0))
        self.assertEqual(main.lerp_color((0, 0, 0), (255, 255, 255), 1.0), (255, 255, 255))
        self.assertEqual(main.lerp_color((0, 0, 0), (100, 200, 50), 0.5), (50, 100, 25))


class TestMainEntrypoint(unittest.TestCase):
    def test_main_writes_entry_png(self):
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, MAKEFUN_OUTPUT_DIR=d)
            r1 = subprocess.run([sys.executable, "main.py"], cwd=os.path.dirname(os.path.abspath(__file__)),
                                env=env, capture_output=True, text=True, timeout=120)
            self.assertEqual(r1.returncode, 0, "main.py failed: %s" % r1.stderr)
            p = os.path.join(d, "entry.png")
            self.assertTrue(os.path.exists(p), "entry.png not written")
            with open(p, "rb") as f:
                b1 = f.read()
            self.assertTrue(b1.startswith(b"\x89PNG"), "not a PNG")
            self.assertLessEqual(len(b1), 1048576)
            r2 = subprocess.run([sys.executable, "main.py"], cwd=os.path.dirname(os.path.abspath(__file__)),
                                env=env, capture_output=True, text=True, timeout=120)
            self.assertEqual(r2.returncode, 0)
            with open(p, "rb") as f:
                b2 = f.read()
            self.assertEqual(b1, b2, "two runs of main.py differ")


if __name__ == "__main__":
    unittest.main()
