"""Sprites: board backgrounds, slots, projectiles, effects, icons. Every function returns an Img."""
import math
import random

from raster import *
import layout
import rigs

OUT = rgb("#2b2233")
GOLD = rgb("#f6c945")


def gradient(img, top, bottom, y0=0, y1=None):
    """Fast vertical gradient over the whole image (direct pixel writes)."""
    y1 = img.h if y1 is None else y1
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        c = [(top[i] + (bottom[i] - top[i]) * t) / 255 for i in range(3)]
        for x in range(img.w):
            i = (y * img.w + x) * 4
            img.px[i], img.px[i + 1], img.px[i + 2], img.px[i + 3] = c[0], c[1], c[2], 1.0


# ---------- board ----------

def make_field():
    """The battlefield: grass with a trodden dirt lane in the middle and scattered tufts and flowers."""
    w, h = layout.W, layout.FIELD_H
    img = Img(w, h)
    gradient(img, (88, 168, 74), (112, 190, 88))
    rnd = random.Random(7)
    for _ in range(40):  # darker patches
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        fill(img, ellipse(x, y, rnd.uniform(20, 46), rnd.uniform(10, 22)), (60, 140, 60, 40), box=(x - 50, y - 26, x + 50, y + 26), ss=1)
    for _ in range(260):  # tufts
        x, y = rnd.uniform(4, w - 4), rnd.uniform(4, h - 4)
        c = rgb(rnd.choice(["#4f9a3a", "#7ccf5c", "#58a841"]))
        fill(img, poly([(x - 3, y + 3), (x - 1, y - 4), (x, y + 3), (x + 2, y - 5), (x + 3, y + 3)]), alpha(c, 200), box=(x - 5, y - 6, x + 5, y + 5), ss=2)
    for _ in range(46):  # flowers
        x, y = rnd.uniform(6, w - 6), rnd.uniform(6, h - 6)
        c = rgb(rnd.choice(["#ffffff", "#ffe066", "#ff8fb1", "#a9d8ff"]))
        fill(img, circle(x, y, 2.4), c, box=(x - 4, y - 4, x + 4, y + 4), ss=2)
        fill(img, circle(x, y, 1.0), rgb("#f6a21c"), box=(x - 2, y - 2, x + 2, y + 2), ss=2)
    # the lane the monsters march down
    lane = Img(w, h)
    cx = w / 2
    fill(lane, rbox(cx, h / 2, 175, h, 0), (228, 200, 140, 255), ss=1, box=(cx - 192, 0, cx + 192, h))
    for _ in range(120):
        x, y = rnd.uniform(cx - 185, cx + 185), rnd.uniform(0, h)
        c = rnd.choice([(190, 158, 100, 140), (232, 208, 152, 140)])
        fill(lane, ellipse(x, y, rnd.uniform(3, 8), rnd.uniform(2, 4)), c, box=(x - 9, y - 5, x + 9, y + 5), ss=1)
    # soften the lane edge by painting it at reduced alpha over the grass
    for i in range(0, len(lane.px), 4):
        a = lane.px[i + 3] * 0.85
        if a > 0:
            k = 1 - a
            img.px[i] = lane.px[i] / max(lane.px[i + 3], 1e-9) * a + img.px[i] * k
            img.px[i + 1] = lane.px[i + 1] / max(lane.px[i + 3], 1e-9) * a + img.px[i + 1] * k
            img.px[i + 2] = lane.px[i + 2] / max(lane.px[i + 3], 1e-9) * a + img.px[i + 2] * k
    return img


def make_wall():
    """The city wall the monsters try to reach: crenellated stone with a shadow under it."""
    w, h = layout.W, 64
    img = Img(w, h)
    stone, stone_d, stone_l = rgb("#b7bdc9"), rgb("#8f97a6"), rgb("#d6dbe4")
    fill(img, rbox(w / 2, 52, w / 2, 7, 0), (0, 0, 0, 70), ss=1, box=(0, 44, w, 64))
    shape(img, rbox(w / 2, 34, w / 2 + 4, 14, 0), stone, OUT, 2, ss=1, box=(0, 16, w, 52))
    for x in range(0, w + 36, 36):  # merlons
        shape(img, rbox(x + 6, 14, 12, 9, 2), stone, OUT, 2, ss=1, box=(x - 10, 0, x + 24, 26))
        fill(img, rbox(x + 6, 9, 9, 2, 0), (255, 255, 255, 90), ss=1, box=(x - 4, 5, x + 18, 14))
    for row in range(3):  # bricks
        y = 24 + row * 9
        fill(img, rbox(w / 2, y, w / 2, 0.6, 0), alpha(stone_d, 200), ss=1, box=(0, y - 1, w, y + 1))
        for x in range(-18 + (row % 2) * 18, w, 36):
            fill(img, rbox(x, y + 4.5, 0.6, 4.5, 0), alpha(stone_d, 200), ss=1, box=(x - 1, y, x + 1, y + 9))
    fill(img, rbox(w / 2, 22, w / 2, 1.2, 0), alpha(stone_l, 200), ss=1, box=(0, 20, w, 24))
    return img


def make_floor():
    """The ground under the slots and the bench."""
    w, h = layout.W, layout.H - 560
    img = Img(w, h)
    gradient(img, (62, 52, 96), (36, 30, 62))
    for x in range(0, w, 54):
        fill(img, rbox(x, h / 2, 0.7, h, 0), (255, 255, 255, 14), ss=1, box=(x - 1, 0, x + 1, h))
    for y in range(0, h, 54):
        fill(img, rbox(w / 2, y, w, 0.7, 0), (255, 255, 255, 14), ss=1, box=(0, y - 1, w, y + 1))
    fill(img, rbox(w / 2, 2, w / 2, 3, 0), (20, 16, 40, 160), ss=1, box=(0, 0, w, 6))
    return img


def make_slot():
    """A battle slot: a stone tile with a golden rim and a rune."""
    s = layout.CELL
    img = Img(s, s)
    shape(img, rbox(s / 2, s / 2, s / 2 - 3, s / 2 - 3, 12), rgb("#59557f"), rgb("#d9b25a"), 2.4)
    fill(img, rbox(s / 2, s / 2 - 1, s / 2 - 9, s / 2 - 9, 8), rgb("#47436a"), ss=3)
    fill(img, rbox(s / 2, 14, s / 2 - 14, 3, 2), (255, 255, 255, 40), ss=2)
    fill(img, ring(s / 2, s / 2, 20, 3), (255, 214, 120, 70), ss=3)
    for a in range(0, 360, 90):  # rune ticks
        x, y = s / 2 + math.cos(math.radians(a)) * 26, s / 2 + math.sin(math.radians(a)) * 26
        fill(img, circle(x, y, 2.2), (255, 214, 120, 90), ss=2)
    for cx, cy in ((12, 12), (s - 12, 12), (12, s - 12), (s - 12, s - 12)):
        shape(img, circle(cx, cy, 3), rgb("#f1d98c"), OUT, 0.8)
    return img


def make_bench_slot():
    """A bench cell: a wooden nest."""
    s = layout.CELL
    img = Img(s, s)
    shape(img, rbox(s / 2, s / 2, s / 2 - 3, s / 2 - 3, 14), rgb("#8a5a34"), OUT, 2.4)
    for y in (26, 48, 70):
        fill(img, rbox(s / 2, y, s / 2 - 10, 0.9, 0), (60, 36, 20, 150), ss=2, box=(8, y - 2, s - 8, y + 2))
    fill(img, rbox(s / 2, s / 2 + 2, s / 2 - 12, s / 2 - 12, 10), rgb("#6a4326"), ss=3)
    fill(img, ellipse(s / 2, s / 2 + 10, 28, 14), (230, 200, 120, 60), ss=2)
    fill(img, rbox(s / 2, 12, s / 2 - 14, 2.5, 2), (255, 255, 255, 50), ss=2)
    return img


def make_slot_hi():
    s = layout.CELL + 10
    img = Img(s, s)
    fill(img, sub(rbox(s / 2, s / 2, s / 2 - 1, s / 2 - 1, 15), rbox(s / 2, s / 2, s / 2 - 6, s / 2 - 6, 11)), (255, 255, 255, 255), ss=3)
    fill(img, sub(rbox(s / 2, s / 2, s / 2 - 1, s / 2 - 1, 15), rbox(s / 2, s / 2, s / 2 - 12, s / 2 - 12, 9)), (255, 255, 255, 70), ss=2)
    return img


# ---------- projectiles / effects ----------

def make_fireball():
    """A white-hot ball with a tail, pointing right; the Sprite tints it per dragon level."""
    w, h = 48, 32
    img = Img(w, h)
    fill(img, ellipse(18, 16, 18, 8), radial(18, 16, 18, (255, 255, 255, 170), (255, 255, 255, 0)), ss=1)
    fill(img, circle(32, 16, 14), radial(32, 16, 14, (255, 255, 255, 255), (255, 255, 255, 0)), ss=1)
    fill(img, circle(33, 16, 7.5), (255, 255, 255, 255), ss=3)
    return img


def make_spark():
    img = Img(16, 16)
    fill(img, circle(8, 8, 8), radial(8, 8, 8, (255, 255, 255, 255), (255, 255, 255, 0)), ss=1)
    return img


def make_ring():
    img = Img(128, 128)
    fill(img, ring(64, 64, 61, 4), (255, 255, 255, 255), ss=3)
    return img


def make_shadow():
    img = Img(48, 16)
    fill(img, ellipse(24, 8, 22, 6.5), radial(24, 8, 24, (0, 0, 0, 130), (0, 0, 0, 0)), ss=1)
    return img


# ---------- icons (48x48) ----------

def make_coin():
    img = Img(48, 48)
    shape(img, circle(24, 24, 20), GOLD, OUT, 2)
    fill(img, ring(24, 24, 13.5, 3), rgb("#d99a1c"), ss=2)
    fill(img, rbox(24, 24, 2.4, 8, 1), rgb("#d99a1c"), ss=2)
    fill(img, ellipse(17, 14, 6, 3), (255, 255, 255, 120), ss=2)
    return img


def make_heart():
    img = Img(48, 48)
    h = union(circle(16.5, 18, 10.5), circle(31.5, 18, 10.5), poly([(6.5, 22), (41.5, 22), (24, 42)]))
    shape(img, h, rgb("#ff4d62"), OUT, 2)
    fill(img, ellipse(15, 14, 5, 3), (255, 255, 255, 130), ss=2)
    return img


def make_wave():
    img = Img(48, 48)
    shape(img, rbox(14, 24, 2.5, 19, 1), rgb("#e9e2d0"), OUT, 1.6)
    shape(img, poly([(16, 8), (40, 15), (16, 25)]), rgb("#ff7a3d"), OUT, 1.8)
    return img


def make_pause():
    img = Img(48, 48)
    for x in (17, 31):
        shape(img, rbox(x, 24, 5, 15, 2), (255, 255, 255, 255), OUT, 2)
    return img


def make_ff():
    img = Img(48, 48)
    shape(img, poly([(6, 10), (24, 24), (6, 38)]), (255, 255, 255, 255), OUT, 2)
    shape(img, poly([(24, 10), (42, 24), (24, 38)]), (255, 255, 255, 255), OUT, 2)
    return img


def make_egg():
    img = Img(48, 48)
    shape(img, union(ellipse(24, 28, 15, 18), circle(24, 20, 12)), rgb("#f4ead0"), OUT, 2)
    for x, y, r in ((18, 24, 3), (29, 30, 3.4), (22, 36, 2.4), (28, 20, 2.2)):
        fill(img, circle(x, y, r), rgb("#7bd25a"), ss=2)
    fill(img, ellipse(18, 16, 4, 6), (255, 255, 255, 120), ss=2)
    return img


# ---------- title screen / app icon ----------

def make_menu_bg():
    w, h = layout.W, layout.H
    img = Img(w, h)
    gradient(img, (255, 168, 108), (92, 70, 150), 0, h)
    rnd = random.Random(3)
    fill(img, circle(w * 0.72, h * 0.3, 70), radial(w * 0.72, h * 0.3, 70, (255, 250, 210, 255), (255, 214, 140, 0)), ss=1)
    fill(img, circle(w * 0.72, h * 0.3, 38), rgb("#fff4c2"), ss=2)
    for _ in range(9):  # clouds
        x, y = rnd.uniform(0, w), rnd.uniform(h * 0.12, h * 0.5)
        for dx, dy, r in ((0, 0, 22), (22, 6, 18), (-22, 7, 16), (8, -9, 16)):
            fill(img, circle(x + dx, y + dy, r), (255, 255, 255, 120), box=(x + dx - r - 2, y + dy - r - 2, x + dx + r + 2, y + dy + r + 2), ss=2)
    for base, col, amp in ((h * 0.66, "#6a4f9a", 90), (h * 0.74, "#4b3a7a", 70)):  # mountains
        pts = [(0, h)]
        x = 0
        while x <= w + 60:
            pts.append((x, base - amp * (0.5 + 0.5 * math.sin(x / 70.0 + base))))
            x += 30
        pts.append((w, h))
        fill(img, poly(pts), rgb(col), ss=1, box=(0, base - amp - 4, w, h))
    # castle
    stone, dark = rgb("#cfd3e0"), rgb("#8f94ad")
    cx, cy = w / 2, h * 0.74
    shape(img, rbox(cx, cy + 10, 70, 44, 3), stone, OUT, 3, ss=2)
    for dx in (-48, 48):
        shape(img, rbox(cx + dx, cy - 22, 17, 56, 3), stone, OUT, 3, ss=2)
        shape(img, poly([(cx + dx - 24, cy - 76), (cx + dx, cy - 112), (cx + dx + 24, cy - 76)]), rgb("#d9503e"), OUT, 3, ss=2)
        shape(img, rbox(cx + dx, cy - 28, 4, 9, 2), OUT, None, ss=2)
    shape(img, rbox(cx, cy - 46, 22, 36, 3), stone, OUT, 3, ss=2)
    shape(img, poly([(cx - 30, cy - 80), (cx, cy - 126), (cx + 30, cy - 80)]), rgb("#d9503e"), OUT, 3, ss=2)
    shape(img, rbox(cx, cy + 22, 14, 22, 12), rgb("#5a3a22"), OUT, 2.5, ss=2)
    fill(img, rbox(cx, h - 40, w, 42, 0), rgb("#3a2f5e"), ss=1, box=(0, h - 82, w, h))
    return img


def make_icon():
    s = 1024
    img = Img(s, s)
    fill(img, rbox(s / 2, s / 2, s / 2, s / 2), vgrad(rgb("#ffb070"), rgb("#6a4fb0"), 0, s), ss=1)
    fill(img, circle(s * 0.78, s * 0.22, 90), rgb("#fff4c2"), ss=1)
    head, pv = rigs.d_head(6.4, rigs.DRAGONS[3])
    img.paste(head, int(s / 2 - head.w / 2), int(s / 2 - head.h / 2 + 40))
    return img
