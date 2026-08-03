#!/usr/bin/env python3
"""
Generate the EcoTrace home-screen icons.

iOS frequently ignores an SVG data-URI apple-touch-icon and falls back to a
screenshot of the page, which is why the old icon looked like nothing. These
are real PNGs.

No Pillow on this machine, so the PNG is encoded by hand and the artwork is
drawn by supersampling a coverage function — slower than a canvas, but it
needs no dependencies and the edges come out clean.
"""

import math
import struct
import zlib

SS = 3  # supersample factor


def write_png(path, w, h, px):
    raw = b"".join(b"\x00" + bytes(px[y * w * 4:(y + 1) * w * 4]) for y in range(h))
    comp = zlib.compress(raw, 9)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    out = b"\x89PNG\r\n\x1a\n"
    out += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    out += chunk(b"IDAT", comp)
    out += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(out)
    return len(out)


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(lerp(c1[i], c2[i], t) for i in range(3))


INK = (5, 35, 26)
G1 = (78, 242, 154)
G2 = (46, 211, 160)
G3 = (23, 184, 176)

# barcode bar widths, in units of the icon's width
BARS = [10, 4, 7, 4, 14, 4, 7, 10, 4, 7, 4, 12]


def shade(x, y, S):
    """Return RGB for a point in the S-sized icon."""
    d = (x / S + y / S) / 2
    base = mix(G1, G2, min(1, d * 1.8)) if d < 0.55 else mix(G2, G3, (d - 0.55) / 0.45)

    # soft highlight, upper left
    dx, dy = x / S - 0.28, y / S - 0.20
    r = math.sqrt(dx * dx + dy * dy) / 0.85
    if r < 1:
        base = mix(base, (255, 255, 255), (1 - r) ** 2 * 0.30)
    return base


def in_ink(x, y, S):
    """
    A leaf silhouette whose interior is cut into barcode stripes.

    The outline is kept solid so the leaf still reads at 40px on a home
    screen; the stripes only appear inside it.
    """
    cx, cy = S * 0.5, S * 0.5
    px, py = x - cx, y - cy

    # rotate into leaf space (45° gives the classic leaf tilt)
    a = math.radians(45)
    rx = px * math.cos(a) - py * math.sin(a)
    ry = px * math.sin(a) + py * math.cos(a)

    # leaf = intersection of two offset circles (a vesica)
    R = S * 0.46
    off = S * 0.235
    d1 = (rx - off) ** 2 + ry ** 2
    d2 = (rx + off) ** 2 + ry ** 2
    if d1 > R * R or d2 > R * R:
        return False

    # solid rim so the shape stays legible when small
    edge = S * 0.045
    Ri = R - edge
    if d1 > Ri * Ri or d2 > Ri * Ri:
        return True

    # midrib along the leaf's long axis
    if abs(ry) < S * 0.018:
        return True

    # Barcode stripes across the interior. Deliberately chunky: thin bars
    # turn into a grey smudge once the icon is 60px on a home screen.
    u = S / 512.0 * 2.15
    period = sum(BARS) * u + len(BARS) * 6 * u
    t = ((x - S * 0.5) % period + period) % period
    acc = 0.0
    for i, w in enumerate(BARS):
        ww = w * u
        if acc <= t < acc + ww:
            return True
        acc += ww + 6 * u
    return False


def render(S, path):
    big = S * SS
    px = bytearray(S * S * 4)

    for y in range(S):
        for x in range(S):
            hits = 0
            rs = gs = bs = 0.0
            for sy in range(SS):
                for sx in range(SS):
                    fx = x * SS + sx + 0.5
                    fy = y * SS + sy + 0.5
                    col = shade(fx / SS, fy / SS, S)
                    if in_ink(fx / SS, fy / SS, S):
                        col = INK
                        hits += 1
                    rs += col[0]; gs += col[1]; bs += col[2]
            n = SS * SS
            i = (y * S + x) * 4
            px[i] = int(rs / n)
            px[i + 1] = int(gs / n)
            px[i + 2] = int(bs / n)
            px[i + 3] = 255

    size = write_png(path, S, S, px)
    print(f"{path}: {S}x{S}, {size/1024:.1f} KB")


render(180, "icon-180.png")
render(512, "icon-512.png")
