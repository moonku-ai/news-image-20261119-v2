"""news-image-20261119 v2 — "THE WORLD IN ONE DAY"

A pure-Python-stdlib program that draws a broadsheet front page summing up
Thursday 19 November 2026 and writes it to /output/entry.png (1024x1024,
PNG, <= 1 MiB). No network, no third-party code, fully deterministic: two
runs write byte-identical files.

Design: a newspaper front page whose one bold element is a drawn neon
Vice City sunset for the day's lead story (GTA VI's worldwide rollout),
then four illustrated story rows and a two-item ticker strip.
Palette: warm newsprint paper, soft-black ink, signal red rules.
Type: one 5x7 bitmap face, all caps, scaled by hierarchy.

Stories (all first reported on, or happening on, 19 November 2026):
  LEAD  GTA VI rolls out worldwide at midnight local time, 13 years
        after GTA V; critics score it 99/100 on Metacritic.
  SPACE NASA marks Voyager 1 one light-day from Earth (16bn miles),
        the first human-made object that far away.
  MIDEAST Israel launches its first ground operation in central Gaza
        since the October 2025 ceasefire.
  ASIA  Cyclone Akvan nears India's Andhra-Odisha coast.
  EUROPE EU proposes a 45bn euro Ukraine loan for 2027.
  STRIP Democrats nominate Hakeem Jeffries for Speaker, 251-11;
        Australia sanctions Israeli settlers over West Bank expansion.
"""
import os
import struct
import zlib

W = 1024
H = 1024
MARGIN = 36

PAPER = (245, 239, 224)
INK = (22, 19, 14)
RED = (200, 16, 46)
NAVY = (14, 42, 74)

MASTHEAD = "THE WORLD IN ONE DAY"
DATE_LINE = "THURSDAY 19 NOVEMBER 2026"
FOOTER = "ALL STORIES FIRST REPORTED ON THURSDAY 19 NOVEMBER 2026"

LEAD = {
    "kicker": "CULTURE - GAMING",
    "headline": ["VICE CITY", "OPENS"],
    "sub": "GTA VI ROLLS OUT WORLDWIDE AFTER A 13-YEAR WAIT - CRITICS SCORE IT 99 OUT OF 100.",
    "tag": "MIDNIGHT LAUNCH WORLDWIDE.",
}
LEAD_TEXT_W = 368

STORIES = [
    {
        "kicker": "SPACE",
        "headline": "ONE LIGHT-DAY FROM HOME",
        "summary": "NASA MARKS VOYAGER 1, NOW 16BN MILES OUT - THE FIRST HUMAN OBJECT A LIGHT-DAY FROM EARTH.",
        "art": "voyager",
    },
    {
        "kicker": "MIDDLE EAST",
        "headline": "TANKS CROSS CEASEFIRE LINE",
        "summary": "ISRAEL LAUNCHES ITS FIRST GROUND OPERATION IN CENTRAL GAZA SINCE THE OCTOBER 2025 TRUCE.",
        "art": "gaza",
    },
    {
        "kicker": "ASIA - WEATHER",
        "headline": "STORM BEARS DOWN ON INDIA",
        "summary": "CYCLONE AKVAN NEARS THE ANDHRA-ODISHA COAST AS AUTHORITIES MOVE PEOPLE TO SAFETY.",
        "art": "cyclone",
    },
    {
        "kicker": "EUROPE",
        "headline": "EU WEIGHS 45BN EURO UKRAINE LOAN",
        "summary": "BRUSSELS PROPOSES A LOAN FOR 2027, TO BE REPAID ONLY ONCE RUSSIA PAYS REPARATIONS.",
        "art": "eu",
    },
]
ROW_TEXT_W = 840

STRIP = [
    {
        "headline": "JEFFRIES PICKED FOR SPEAKER",
        "summary": "DEMOCRATS NOMINATE HIM 251-11. HE WOULD BE THE FIRST BLACK SPEAKER.",
    },
    {
        "headline": "AUSTRALIA SANCTIONS SETTLERS",
        "summary": "CANBERRA ACTS OVER WEST BANK EXPANSION.",
    },
]

# ---------------------------------------------------------------- font
# 5x7 bitmap face: each glyph is 7 rows of 5 characters ('#' = ink).
_G = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00000", "00100"),
    ",": ("00000", "00000", "00000", "00000", "00000", "01100", "00100"),
    ":": ("00000", "00100", "00100", "00000", "00100", "00100", "00000"),
    ";": ("00000", "00100", "00100", "00000", "00100", "01100", "00100"),
    "'": ("00100", "00100", "00000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
}
FONT = {k: tuple(row.replace("0", ".").replace("1", "#") for row in v)
        for k, v in _G.items()}


def text_width(text, scale):
    """Drawn width in px of text at scale (5px glyph + 1px gap, no trailing gap)."""
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def wrap_text(text, max_w, scale):
    """Greedy word wrap; splits over-long words by character."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = ""
            while text_width(word, scale) > max_w:
                # take as many chars as fit
                n = max(1, (max_w + scale) // (6 * scale))
                lines.append(word[:n])
                word = word[n:]
            cur = word
    if cur:
        lines.append(cur)
    return lines


def lerp_color(c0, c1, t):
    return tuple(int(round(c0[i] + (c1[i] - c0[i]) * t)) for i in range(3))


def _lcg(seed):
    """Deterministic pseudo-random generator (fixed seed -> fixed art)."""
    state = seed & 0xFFFFFFFF

    def nxt():
        nonlocal state
        state = (state * 1664525 + 1013904223) & 0xFFFFFFFF
        return state / 4294967296.0

    return nxt


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg=PAPER):
        self.w, self.h = w, h
        self.buf = bytearray(w * h * 3)
        self.oob = 0
        self.clip = None  # (x0, y0, x1, y1) exclusive, or None
        row = bytes(bg) * w
        for y in range(h):
            self.buf[y * w * 3:(y + 1) * w * 3] = row

    def push_clip(self, x, y, w, h):
        self.clip = (x, y, x + w, y + h)

    def pop_clip(self):
        self.clip = None

    def _inside(self, x, y):
        if not (0 <= x < self.w and 0 <= y < self.h):
            return False
        if self.clip is not None:
            cx0, cy0, cx1, cy1 = self.clip
            if not (cx0 <= x < cx1 and cy0 <= y < cy1):
                return False
        return True

    def set_pixel(self, x, y, color):
        if self.clip is not None:
            cx0, cy0, cx1, cy1 = self.clip
            if not (cx0 <= x < cx1 and cy0 <= y < cy1):
                return  # intentionally clipped by the panel, not out of bounds
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)
        else:
            self.oob += 1

    def fill_rect(self, x, y, w, h, color):
        if w <= 0 or h <= 0:
            return
        if self.clip is None and 0 <= x and 0 <= y and x + w <= self.w and y + h <= self.h:
            row = bytes(color) * w
            for yy in range(y, y + h):
                i = (yy * self.w + x) * 3
                self.buf[i:i + w * 3] = row
        else:
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    self.set_pixel(xx, yy, color)

    def hline(self, x, y, w, color):
        self.fill_rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.fill_rect(x, y, 1, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def thick_line(self, x0, y0, x1, y1, width, color):
        # stamp width x width squares along the Bresenham path
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        half = width // 2
        while True:
            self.fill_rect(x0 - half, y0 - half, width, width, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def ring(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.set_pixel(cx - dx, cy + dy, color)
            self.set_pixel(cx + dx, cy + dy, color)

    def vgradient(self, x, y, w, h, c0, c1):
        for i in range(h):
            t = i / max(1, h - 1)
            self.fill_rect(x, y + i, w, 1, lerp_color(c0, c1, t))

    def vgradient3(self, x, y, w, h, c0, c1, c2):
        mid = h // 2
        self.vgradient(x, y, w, mid, c0, c1)
        self.vgradient(x, y + mid, w, h - mid, c1, c2)

    def draw_text(self, x, y, text, scale, color):
        cx = x
        for ch in text:
            glyph = FONT.get(ch)
            if glyph is None:
                cx += 6 * scale
                continue
            for r, row in enumerate(glyph):
                for c, px in enumerate(row):
                    if px == "#":
                        self.fill_rect(cx + c * scale, y + r * scale, scale, scale, color)
            cx += 6 * scale

    def draw_text_centered(self, y, text, scale, color):
        self.draw_text((self.w - text_width(text, scale)) // 2, y, text, scale, color)


# ---------------------------------------------------------------- art panels
def draw_lead_art(cv, x, y, w, h):
    """Neon Vice City sunset: gradient sky, sun, skyline, palms, big VI."""
    cv.push_clip(x, y, w, h)
    cv.vgradient3(x, y, w, h, (43, 26, 78), (255, 122, 26), (255, 46, 136))
    # sun with glow
    cv.circle(x + 170, y + 105, 60, (255, 170, 80))
    cv.circle(x + 170, y + 105, 52, (255, 236, 170))
    # neon VI (glow pass then core pass)
    for width, color in ((22, (0, 90, 120)), (12, (25, 211, 255))):
        cv.thick_line(x + 392, y + 32, x + 432, y + 152, width, color)
        cv.thick_line(x + 432, y + 152, x + 472, y + 32, width, color)
    for width, color in ((22, (150, 10, 80)), (12, (255, 46, 136))):
        cv.thick_line(x + 502, y + 32, x + 502, y + 152, width, color)
        cv.thick_line(x + 484, y + 32, x + 520, y + 32, width, color)
        cv.thick_line(x + 484, y + 152, x + 520, y + 152, width, color)
    # skyline with lit windows (deterministic)
    rnd = _lcg(7)
    bx = x
    while bx < x + w:
        bw = 34 + int(rnd() * 28)
        bh = 60 + int(rnd() * 62)
        by = y + h - bh
        cv.fill_rect(bx, by, bw, bh, (24, 12, 44))
        for wy in range(by + 8, y + h - 10, 12):
            for wx in range(bx + 5, bx + bw - 5, 10):
                if rnd() < 0.45:
                    cv.fill_rect(wx, wy, 4, 6, (255, 205, 90))
        bx += bw + 2
    # ground strip
    cv.fill_rect(x, y + h - 22, w, 22, (16, 8, 30))
    # palms
    for px, py, lean in ((x + 62, y + h - 22, -1), (x + 512, y + h - 22, 1)):
        cv.thick_line(px, py, px + 14 * lean, py - 62, 5, (16, 8, 30))
        top = (px + 14 * lean, py - 62)
        for ang in (-70, -35, 0, 35, 70):
            import math
            dx = int(34 * math.sin(math.radians(ang)))
            dy = -int(20 * math.cos(math.radians(ang))) + 12
            cv.line(top[0], top[1], top[0] + dx, top[1] + dy, (16, 8, 30))
    cv.pop_clip()


def draw_voyager_art(cv, x, y, w, h):
    cv.push_clip(x, y, w, h)
    cv.fill_rect(x, y, w, h, (10, 24, 54))
    rnd = _lcg(3)
    for _ in range(16):
        cv.set_pixel(x + int(rnd() * w), y + int(rnd() * (h - 30)), (220, 230, 255))
    # Earth rising at bottom-left
    cv.circle(x + 8, y + h + 18, 58, (52, 120, 210))
    cv.circle(x + 8, y + h + 18, 50, (120, 180, 255))
    # satellite: gold body, blue panels, dish, antenna
    cv.fill_rect(x + 44, y + 30, 24, 14, (220, 180, 60))
    cv.fill_rect(x + 22, y + 33, 20, 8, (40, 80, 180))
    cv.fill_rect(x + 70, y + 33, 20, 8, (40, 80, 180))
    cv.line(x + 56, y + 30, x + 56, y + 16, (220, 180, 60))
    cv.set_pixel(x + 56, y + 14, (255, 240, 160))
    # dashed signal to Earth
    for i in range(0, 5):
        cv.line(x + 48 - i * 3, y + 52 + i * 6, x + 45 - i * 3, y + 56 + i * 6, (255, 240, 160))
    cv.pop_clip()


def draw_gaza_art(cv, x, y, w, h):
    cv.push_clip(x, y, w, h)
    cv.vgradient(x, y, w, h, (201, 168, 106), (138, 109, 59))
    cv.circle(x + 74, y + 18, 10, (255, 220, 150))
    # tents
    for tx in (x + 6, x + 22):
        cv.line(tx, y + 78, tx + 9, y + 64, (240, 230, 200))
        cv.line(tx + 9, y + 64, tx + 18, y + 78, (240, 230, 200))
        cv.line(tx, y + 78, tx + 18, y + 78, (240, 230, 200))
    # road
    cv.thick_line(x, y + 82, x + w, y + 66, 9, (90, 70, 45))
    # tank silhouette
    cv.fill_rect(x + 30, y + 52, 40, 14, (45, 42, 28))
    cv.fill_rect(x + 42, y + 44, 18, 8, (45, 42, 28))
    cv.thick_line(x + 58, y + 47, x + 78, y + 44, 3, (45, 42, 28))
    for wx in (x + 36, x + 48, x + 60):
        cv.circle(wx, y + 68, 4, (20, 18, 12))
    cv.pop_clip()


def draw_cyclone_art(cv, x, y, w, h):
    cv.push_clip(x, y, w, h)
    cv.vgradient(x, y, w, h, (15, 94, 110), (8, 48, 70))
    cx, cy = x + 48, y + 44
    # spiral as alternating rings
    for r, col in ((34, (220, 240, 245)), (27, (15, 94, 110)), (20, (220, 240, 245)),
                   (13, (8, 48, 70)), (7, (220, 240, 245))):
        cv.circle(cx, cy, r, col)
    # rain streaks
    for i in range(8):
        rx = x + 6 + i * 11
        cv.line(rx, y + 78, rx - 5, y + 92, (200, 230, 240))
    cv.pop_clip()


def draw_eu_art(cv, x, y, w, h):
    cv.push_clip(x, y, w, h)
    cv.fill_rect(x, y, w, h, (34, 64, 154))
    # ring of 12 stars
    import math
    for i in range(12):
        a = math.radians(i * 30)
        sx = int(x + 48 + 30 * math.cos(a))
        sy = int(y + 44 + 30 * math.sin(a))
        cv.fill_rect(sx - 1, sy - 3, 3, 7, (255, 210, 60))
        cv.fill_rect(sx - 3, sy - 1, 7, 3, (255, 210, 60))
    # coins
    for cx, cy in ((x + 28, y + 80), (x + 48, y + 84), (x + 68, y + 80)):
        cv.circle(cx, cy, 10, (255, 210, 60))
        cv.circle(cx, cy, 6, (200, 160, 40))
    cv.pop_clip()


ART = {
    "voyager": draw_voyager_art,
    "gaza": draw_gaza_art,
    "cyclone": draw_cyclone_art,
    "eu": draw_eu_art,
}


# ---------------------------------------------------------------- layout
def draw_front_page(cv):
    # masthead
    cv.draw_text_centered(30, MASTHEAD, 6, INK)
    cv.draw_text_centered(86, DATE_LINE, 3, RED)
    cv.fill_rect(MARGIN, 122, W - 2 * MARGIN, 4, RED)
    cv.fill_rect(MARGIN, 130, W - 2 * MARGIN, 2, INK)

    # lead story
    ly = 150
    draw_lead_art(cv, MARGIN, ly, 560, 300)
    tx = 620
    cv.draw_text(tx, ly + 12, LEAD["kicker"], 2, RED)
    hy = ly + 40
    for line in LEAD["headline"]:
        cv.draw_text(tx, hy, line, 6, INK)
        hy += 48  # 42px glyphs + 6px leading so lines never touch
    cv.fill_rect(tx, ly + 140, LEAD_TEXT_W, 3, RED)
    sy = ly + 154
    for line in wrap_text(LEAD["sub"], LEAD_TEXT_W, 2):
        cv.draw_text(tx, sy, line, 2, INK)
        sy += 16
    cv.draw_text(tx, ly + 222, LEAD["tag"], 2, RED)

    # hairline under lead
    cv.fill_rect(MARGIN, 462, W - 2 * MARGIN, 2, INK)

    # story rows
    ry = 474
    for s in STORIES:
        ART[s["art"]](cv, MARGIN, ry + 4, 96, 96)
        tx = 148
        cv.draw_text(tx, ry + 8, s["kicker"], 2, RED)
        cv.draw_text(tx, ry + 28, s["headline"], 3, INK)
        sy = ry + 58
        for line in wrap_text(s["summary"], ROW_TEXT_W, 2):
            cv.draw_text(tx, sy, line, 2, INK)
            sy += 16
        ry += 104

    # hairline above strip
    cv.fill_rect(MARGIN, 896, W - 2 * MARGIN, 2, INK)

    # ticker strip: two mini stories
    for i, s in enumerate(STRIP):
        sx = MARGIN + i * 494  # col 1 at 36, col 2 at 530; rule at 518
        cv.draw_text(sx, 910, s["headline"], 2, INK)
        sy = 932
        for line in wrap_text(s["summary"], 458, 2):
            cv.draw_text(sx, sy, line, 2, INK)
            sy += 16
    cv.vline(518, 908, 68, INK)

    # footer
    cv.draw_text_centered(988, FOOTER, 2, RED)


# ---------------------------------------------------------------- png
def _chunk(ctype, data):
    out = struct.pack(">I", len(data)) + ctype + data
    return out + struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)


def render_png():
    cv = Canvas(W, H)
    draw_front_page(cv)
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += cv.buf[y * W * 3:(y + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return png


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    data = render_png()
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
