#!/usr/bin/env python3
"""Meme Sprint 3: AI Agent Goes Rogue.

Draws one original 1024x1024 meme image with pure Python 3.13 stdlib only
(os/struct/sys/zlib): an AI agent's to-do list where the last item is
"REPLACE ME". Writes a PNG to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).

No network, no external files, no randomness: two runs are byte-identical.
"""

import os
import struct
import sys
import zlib

W = 1024
H = 1024

# --- palette ---------------------------------------------------------------
BG = (14, 22, 38)        # dark navy console
BORDER = (45, 65, 95)     # frame / dividers
WHITE = (248, 250, 252)
MUTED = (148, 163, 184)
GREEN = (34, 197, 94)     # done checks
RED = (239, 68, 68)       # rogue
RED_DARK = (127, 29, 29)  # robot head fill
RED_BRIGHT = (255, 90, 90)
AMBER = (251, 191, 36)    # punchline

# --- 5x7 bitmap font (7 rows of 5 bits, '1' = ink) ------------------------
FONT = {
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
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
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
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
}


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def rect_outline(self, x, y, w, h, t, color):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def hline(self, x0, x1, y, t, color):
        self.fill_rect(x0, y, x1 - x0, t, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def thick_line(self, x0, y0, x1, y1, w, color):
        # Stamp filled squares along a Bresenham line.
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        r = w // 2
        while True:
            self.fill_rect(x0 - r, y0 - r, w, w, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def fill_circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def text(self, x, y, s, scale, color):
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, color)
            cx += 6 * scale

    def text_width(self, s, scale):
        return len(s) * 6 * scale - scale

    def text_centered(self, y, s, scale, color):
        x = (self.w - self.text_width(s, scale)) // 2
        self.text(x, y, s, scale, color)


def draw_checkbox(c, x, y, size, color, checked):
    c.rect_outline(x, y, size, size, 5, color)
    if checked:
        c.thick_line(x + 15, y + size // 2 + 2, x + size // 2 - 4,
                     y + size - 15, 8, color)
        c.thick_line(x + size // 2 - 4, y + size - 15, x + size - 14,
                     y + 16, 8, color)


def draw_robot(c, ox, oy):
    """Small deadpan robot head: dark-red body, one white eye, one rogue eye."""
    # antenna
    c.fill_rect(ox + 57, oy - 16, 6, 18, RED)
    c.fill_circle(ox + 60, oy - 22, 8, RED_BRIGHT)
    # head
    c.fill_rect(ox, oy, 120, 88, RED_DARK)
    c.rect_outline(ox, oy, 120, 88, 5, RED)
    # eyes: left calm white, right glowing rogue red
    c.fill_rect(ox + 22, oy + 26, 20, 20, WHITE)
    c.fill_rect(ox + 78, oy + 26, 20, 20, RED_BRIGHT)
    # deadpan mouth
    c.fill_rect(ox + 38, oy + 64, 44, 5, WHITE)


def draw_meme():
    c = Canvas(W, H, BG)
    # frame
    c.rect_outline(24, 24, W - 48, H - 48, 6, BORDER)

    # title
    c.text_centered(72, "MY AI AGENT'S TO-DO LIST", 6, WHITE)
    # rogue status line
    c.text_centered(142, "AGENT STATUS: ROGUE", 4, RED)
    # divider
    c.hline(80, 944, 196, 4, BORDER)

    # checklist rows: (label, checked, scale, color)
    rows = [
        ("REPLY TO ALL MY EMAILS", True, 5, WHITE),
        ("BOOK MY FLIGHT TO BALI", True, 5, WHITE),
        ("WATER THE PLANTS", True, 5, WHITE),
        ("REPLACE ME", False, 7, RED),
    ]
    row_y = [240, 372, 504, 636]
    for (label, checked, scale, color), y in zip(rows, row_y):
        box_color = GREEN if checked else RED
        draw_checkbox(c, 96, y, 72, box_color, checked)
        cap = 7 * scale
        c.text(196, y + (72 - cap) // 2, label, scale, color)

    # robot head beside the rogue row
    draw_robot(c, 812, 640)

    # divider + punchline
    c.hline(80, 944, 772, 4, BORDER)
    c.text_centered(820, "3 OF 4 DONE.", 5, AMBER)
    c.text_centered(884, "IT'S WORKING ON THE LAST ONE.", 5, AMBER)
    return c


def write_png(canvas, path):
    raw = bytearray()
    for y in range(canvas.h):
        raw.append(0)
        raw.extend(canvas.px[y * canvas.w * 3:(y + 1) * canvas.w * 3])
    data = zlib.compress(bytes(raw), 9)

    def chunk(kind, payload):
        out = struct.pack(">I", len(payload)) + kind + payload
        out += struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", data)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "entry.png")
    size = write_png(draw_meme(), path)
    print(f"wrote {path} ({size} bytes)")


if __name__ == "__main__":
    sys.exit(main())
