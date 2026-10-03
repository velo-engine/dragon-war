"""Tiny software rasterizer: signed-distance shapes -> antialiased RGBA images -> PNG (no third-party packages)."""
import math
import struct
import zlib


class Img:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [0.0] * (w * h * 4)  # premultiplied r, g, b, a in 0..1

    def blend(self, x, y, r, g, b, a):
        if a <= 0 or x < 0 or y < 0 or x >= self.w or y >= self.h:
            return
        i = (y * self.w + x) * 4
        p = self.px
        k = 1 - a
        p[i] = r * a + p[i] * k
        p[i + 1] = g * a + p[i + 1] * k
        p[i + 2] = b * a + p[i + 2] * k
        p[i + 3] = a + p[i + 3] * k

    def paste(self, other, ox, oy):
        for y in range(other.h):
            for x in range(other.w):
                i = (y * other.w + x) * 4
                a = other.px[i + 3]
                if a <= 0:
                    continue
                # other is premultiplied
                j = ((oy + y) * self.w + (ox + x)) * 4
                if ox + x < 0 or oy + y < 0 or ox + x >= self.w or oy + y >= self.h:
                    continue
                k = 1 - a
                for c in range(3):
                    self.px[j + c] = other.px[i + c] + self.px[j + c] * k
                self.px[j + 3] = a + self.px[j + 3] * k

    def png(self):
        rows = []
        for y in range(self.h):
            row = bytearray([0])
            for x in range(self.w):
                i = (y * self.w + x) * 4
                a = self.px[i + 3]
                if a <= 0:
                    row += b"\x00\x00\x00\x00"
                    continue
                row.append(min(255, int(self.px[i] / a * 255 + 0.5)))
                row.append(min(255, int(self.px[i + 1] / a * 255 + 0.5)))
                row.append(min(255, int(self.px[i + 2] / a * 255 + 0.5)))
                row.append(min(255, int(a * 255 + 0.5)))
            rows.append(bytes(row))
        raw = b"".join(rows)

        def chunk(tag, data):
            c = struct.pack(">I", len(data)) + tag + data
            return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

        return (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b"")
        )

    def save(self, path):
        with open(path, "wb") as f:
            f.write(self.png())


# ---------- signed distance fields (negative inside) ----------

def circle(cx, cy, r):
    return lambda x, y: math.hypot(x - cx, y - cy) - r


def ellipse(cx, cy, rx, ry):
    m = min(rx, ry)
    return lambda x, y: (math.hypot((x - cx) / rx, (y - cy) / ry) - 1) * m


def rbox(cx, cy, hw, hh, r=0):
    r = min(r, hw, hh)

    def f(x, y):
        dx = abs(x - cx) - (hw - r)
        dy = abs(y - cy) - (hh - r)
        return math.hypot(max(dx, 0), max(dy, 0)) + min(max(dx, dy), 0) - r

    return f


def seg(x1, y1, x2, y2, r):
    vx, vy = x2 - x1, y2 - y1
    L = vx * vx + vy * vy or 1e-9

    def f(x, y):
        t = max(0, min(1, ((x - x1) * vx + (y - y1) * vy) / L))
        return math.hypot(x - (x1 + vx * t), y - (y1 + vy * t)) - r

    return f


def poly(pts):
    n = len(pts)

    def f(x, y):
        d = 1e18
        inside = False
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            vx, vy = bx - ax, by - ay
            L = vx * vx + vy * vy or 1e-9
            t = max(0, min(1, ((x - ax) * vx + (y - ay) * vy) / L))
            d = min(d, math.hypot(x - (ax + vx * t), y - (ay + vy * t)))
            if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
                inside = not inside
        return -d if inside else d

    return f


def ring(cx, cy, r, w):
    return lambda x, y: abs(math.hypot(x - cx, y - cy) - r) - w / 2


def rot(sdf, cx, cy, deg):
    c, s = math.cos(math.radians(-deg)), math.sin(math.radians(-deg))

    def f(x, y):
        dx, dy = x - cx, y - cy
        return sdf(cx + dx * c - dy * s, cy + dx * s + dy * c)

    return f


def union(*fs):
    return lambda x, y: min(f(x, y) for f in fs)


def sub(a, b):
    return lambda x, y: max(a(x, y), -b(x, y))


def inter(a, b):
    return lambda x, y: max(a(x, y), b(x, y))


# ---------- painting ----------

def rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def shade(c, k):
    """k > 0 lightens toward white, k < 0 darkens."""
    r, g, b, a = c
    if k >= 0:
        return (int(r + (255 - r) * k), int(g + (255 - g) * k), int(b + (255 - b) * k), a)
    k = -k
    return (int(r * (1 - k)), int(g * (1 - k)), int(b * (1 - k)), a)


def alpha(c, a):
    return (c[0], c[1], c[2], a)


def fill(img, sdf, color, grow=0.0, ss=3, box=None):
    """Paint where sdf <= grow. `color` is an (r,g,b,a) tuple or a function (x, y) -> tuple."""
    x0, y0, x1, y1 = box or (0, 0, img.w, img.h)
    x0, y0 = max(0, int(x0)), max(0, int(y0))
    x1, y1 = min(img.w, int(math.ceil(x1))), min(img.h, int(math.ceil(y1)))
    n = ss * ss
    for y in range(y0, y1):
        for x in range(x0, x1):
            d = sdf(x + 0.5, y + 0.5) - grow
            if d > 1.2:
                continue
            if d < -1.2:
                cov = 1.0
            else:
                hit = 0
                for sy in range(ss):
                    for sx in range(ss):
                        if sdf(x + (sx + 0.5) / ss, y + (sy + 0.5) / ss) <= grow:
                            hit += 1
                cov = hit / n
            if cov <= 0:
                continue
            c = color(x + 0.5, y + 0.5) if callable(color) else color
            img.blend(x, y, c[0] / 255, c[1] / 255, c[2] / 255, cov * c[3] / 255)


def shape(img, sdf, color, outline=None, ow=1.6, box=None, ss=3):
    """Outlined shape: the outline is the shape grown by `ow`."""
    if outline:
        fill(img, sdf, outline, grow=ow, box=_grow(box, ow), ss=ss)
    fill(img, sdf, color, box=box, ss=ss)


def _grow(box, g):
    if box is None:
        return None
    return (box[0] - g - 1, box[1] - g - 1, box[2] + g + 1, box[3] + g + 1)


def vgrad(top, bottom, y0, y1):
    def f(x, y):
        t = max(0.0, min(1.0, (y - y0) / (y1 - y0)))
        return tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(4))

    return f


def radial(cx, cy, r, inner, outer):
    def f(x, y):
        t = max(0.0, min(1.0, math.hypot(x - cx, y - cy) / r))
        return tuple(int(inner[i] + (outer[i] - inner[i]) * t) for i in range(4))

    return f
