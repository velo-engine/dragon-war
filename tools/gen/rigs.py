"""Kine2D characters written in the format of the Kine2D editor's BUILD button (<name>.skel.json + <name>.atlas.json + <name>.png):
six dragons (one per merge level) and four front-facing enemies.

Bone x/y are absolute (not relative to the parent) in canvas units; with canvasSize 100x180 one unit is one pixel, the origin is
the canvas center. All bones are root bones, so every animation frame is computed here: rest position + a small per-bone delta.
"""
import math

from raster import *

OUT = rgb("#2b2233")


class Part:
    def __init__(self, name, img, pivot, pos, bone_name=None):
        self.name, self.img, self.pivot, self.pos = name, img, pivot, pos
        self.bone = bone_name or name


# ---------------------------------------------------------------- dragons

DRAGONS = [
    dict(name="Hatchling", body="#7bd25a", belly="#f1f7b5", wing="#4fae3e", horn="#f4ecc8", accent="#ffd34a", k=0.92, horns=1, crest=0, crown=0, wing_k=0.9, aura=None, eye="#ffffff"),
    dict(name="Frostling", body="#58b0ff", belly="#dff2ff", wing="#3079d8", horn="#f4f0e0", accent="#9fe6ff", k=0.97, horns=1, crest=0, crown=0, wing_k=1.0, aura=None, eye="#ffffff"),
    dict(name="Stormwing", body="#a874f2", belly="#f4e2ff", wing="#7c46cc", horn="#f6ecd0", accent="#ffe066", k=1.02, horns=2, crest=1, crown=0, wing_k=1.1, aura=None, eye="#ffffff"),
    dict(name="Emberdrake", body="#f0604c", belly="#ffe2a2", wing="#c63a2e", horn="#f8e8c0", accent="#ffb23a", k=1.07, horns=2, crest=2, crown=0, wing_k=1.2, aura=None, eye="#fff2a8"),
    dict(name="Sunlord", body="#ffc83a", belly="#fff4c0", wing="#e8981c", horn="#fffbe8", accent="#ff6a3a", k=1.12, horns=2, crest=2, crown=1, wing_k=1.3, aura=(255, 210, 90), eye="#ff6a3a"),
    dict(name="Inferno", body="#3f3358", belly="#ffa13c", wing="#e0452a", horn="#ffd8a0", accent="#ff4a2a", k=1.18, horns=3, crest=3, crown=2, wing_k=1.42, aura=(255, 90, 50), eye="#ffe14a"),
]

DRAGON_TOP = -62  # roughly where the head top is at k=1, used for the level badge


def d_body(k, c):
    W, H = int(54 * k) + 8, int(58 * k) + 8
    img = Img(W, H)
    cx, cy = W / 2, H / 2
    body, belly = rgb(c["body"]), rgb(c["belly"])
    shape(img, ellipse(cx, cy, 26 * k, 28 * k), body, OUT, 1.6)
    fill(img, ellipse(cx - 9 * k, cy - 12 * k, 8 * k, 5 * k), (255, 255, 255, 55), ss=2)
    shape(img, ellipse(cx, cy + 3 * k, 15 * k, 22 * k), belly, shade(belly, -0.3), 1.0)
    for j in range(5):
        y = cy - 12 * k + j * 7.4 * k
        w = 13 * k * (1 - abs(y - cy - 3 * k) / (26 * k)) + 2
        fill(img, seg(cx - w, y, cx + w, y, 0.8 * k), shade(belly, -0.2), ss=2)
    if c["crest"] >= 3:  # glowing belly gem
        shape(img, circle(cx, cy - 6 * k, 4.2 * k), rgb("#ffe14a"), OUT, 1)
    return img, (cx, cy)


def d_head(k, c):
    W, H = int(66 * k), int(66 * k)
    img = Img(W, H)
    cx = W / 2
    hr = 17 * k
    hy = H - 6 * k - hr * 1.12
    body, belly, horn, accent = rgb(c["body"]), rgb(c["belly"]), rgb(c["horn"]), rgb(c["accent"])
    body_d = shade(body, -0.28)
    pivot = (cx, hy + hr * 0.9)
    # side fins
    for s in (-1, 1):
        shape(img, poly([(cx + s * (hr - 2 * k), hy - 5 * k), (cx + s * (hr + 10 * k), hy - 8 * k), (cx + s * (hr + 6 * k), hy + 1 * k), (cx + s * (hr + 9 * k), hy + 7 * k), (cx + s * (hr - 2 * k), hy + 6 * k)]), body_d, OUT, 1.3)
    # horns (behind the head)
    for s in (-1, 1):
        h = 13 + 4 * c["horns"]
        shape(img, poly([(cx + s * 6 * k, hy - hr + 3 * k), (cx + s * 12 * k, hy - hr - h * 0.45 * k), (cx + s * 17 * k, hy - hr - h * k), (cx + s * 14 * k, hy - hr - 2 * k), (cx + s * 11 * k, hy - hr + 7 * k)]), horn, OUT, 1.2)
        if c["horns"] >= 3:
            shape(img, poly([(cx + s * 15 * k, hy - 6 * k), (cx + s * 26 * k, hy - 14 * k), (cx + s * 18 * k, hy - 1 * k)]), horn, OUT, 1.1)
    shape(img, circle(cx, hy, hr), body, OUT, 1.6)
    fill(img, ellipse(cx - 5 * k, hy - 9 * k, 7 * k, 3.2 * k), (255, 255, 255, 70), ss=2)
    # crest
    for i in range(c["crest"]):
        yy = hy - hr + 1 * k
        xx = cx + (i - (c["crest"] - 1) / 2) * 7 * k
        shape(img, poly([(xx - 3.2 * k, yy + 4 * k), (xx, yy - (5 + 3 * (1 - abs(i - (c["crest"] - 1) / 2) / 2)) * k), (xx + 3.2 * k, yy + 4 * k)]), accent, OUT, 1.0)
    # snout
    shape(img, ellipse(cx, hy + 7 * k, 10 * k, 7 * k), shade(body, 0.28), shade(body, -0.35), 1.0)
    for s in (-1, 1):
        fill(img, ellipse(cx + s * 4 * k, hy + 5 * k, 1.5 * k, 1.1 * k), OUT, ss=2)
    fill(img, seg(cx - 6 * k, hy + 10.5 * k, cx, hy + 12 * k, 0.8 * k), OUT, ss=2)
    fill(img, seg(cx, hy + 12 * k, cx + 6 * k, hy + 10.5 * k, 0.8 * k), OUT, ss=2)
    for s in (-1, 1):  # fangs
        fill(img, poly([(cx + s * 4.6 * k - 1.2 * k, hy + 11 * k), (cx + s * 4.6 * k + 1.2 * k, hy + 11 * k), (cx + s * 4.6 * k, hy + 14.2 * k)]), rgb("#ffffff"), ss=2)
    # eyes
    eye = rgb(c["eye"])
    for s in (-1, 1):
        ex, ey = cx + s * 7.6 * k, hy - 3 * k
        shape(img, circle(ex, ey, 4.6 * k), eye, OUT, 1.0)
        fill(img, ellipse(ex + s * 0.4 * k, ey + 0.3 * k, 1.5 * k, 3.4 * k), OUT, ss=2)
        fill(img, circle(ex - 1.2 * k, ey - 1.6 * k, 1.1 * k), (255, 255, 255, 255), ss=2)
        fill(img, seg(ex - s * 5.5 * k, ey - 6.5 * k + (0 if s < 0 else 0), ex + s * 4 * k, ey - 4 * k - (2 * k), 1.0 * k), OUT, ss=2)
    for s in (-1, 1):  # cheeks
        fill(img, ellipse(cx + s * 12.5 * k, hy + 4.5 * k, 3 * k, 2 * k), (255, 120, 140, 90), ss=2)
    # crown
    if c["crown"]:
        gold = rgb("#ffd447") if c["crown"] == 1 else rgb("#ff6a2a")
        cy0 = hy - hr + 2 * k
        pts = [(cx - 11 * k, cy0 + 1 * k), (cx - 11 * k, cy0 - 7 * k), (cx - 5.5 * k, cy0 - 2 * k), (cx, cy0 - 10 * k), (cx + 5.5 * k, cy0 - 2 * k), (cx + 11 * k, cy0 - 7 * k), (cx + 11 * k, cy0 + 1 * k)]
        shape(img, poly(pts), gold, OUT, 1.2)
        fill(img, circle(cx, cy0 - 4 * k, 1.8 * k), rgb("#ff3a5a") if c["crown"] == 1 else rgb("#fff0a0"), ss=2)
    return img, pivot


def d_wing(k, c, side):
    """side = +1 right wing (spreads to the right), -1 left. Pivot at the shoulder."""
    W, H = int(46 * k), int(44 * k)
    img = Img(W, H)
    wing, accent = rgb(c["wing"]), rgb(c["accent"])

    def X(x):
        return x if side > 0 else W - x

    base = (X(3), H - 6)
    tips = [(X(W * 0.16), H * 0.12), (X(W * 0.5), H * 0.0 + 3), (X(W - 3), H * 0.34)]
    pts = [base, tips[0], (X(W * 0.33), H * 0.38), tips[1], (X(W * 0.62), H * 0.5), tips[2], (X(W * 0.76), H * 0.72), (X(W * 0.5), H * 0.82), (X(W * 0.3), H - 3)]
    shape(img, poly(pts), wing, OUT, 1.4)
    for t in tips:
        fill(img, seg(base[0], base[1], t[0], t[1], 1.0 * k), shade(wing, -0.4), ss=2)
    fill(img, ellipse(X(W * 0.4), H * 0.55, 7 * k, 4 * k), shade(wing, 0.25), ss=2)
    shape(img, circle(base[0], base[1], 3 * k), accent, OUT, 1.0)
    return img, base


def d_foot(k, c):
    W, H = int(20 * k), int(14 * k)
    img = Img(W, H)
    cx = W / 2
    body = rgb(c["body"])
    shape(img, ellipse(cx, H * 0.4, 8 * k, 5.4 * k), shade(body, 0.05), OUT, 1.3)
    for dx in (-4.4, 0, 4.4):
        fill(img, poly([(cx + (dx - 1.6) * k, H * 0.62), (cx + (dx + 1.6) * k, H * 0.62), (cx + dx * 1.15 * k, H - 1)]), rgb(c["horn"]), ss=2)
    return img, (cx, 2)


def d_tail(k, c):
    W, H = int(44 * k), int(40 * k)
    img = Img(W, H)
    body, accent = rgb(c["body"]), rgb(c["accent"])
    pts = []
    for i in range(0, 11):
        t = i / 10
        pts.append((3 + t * (W - 12) + math.sin(t * 3.0) * 2, 4 + t * (H - 14) + math.sin(t * 5) * 3))
    for i in range(10):
        r = (6.6 - 4.0 * i / 10) * k
        shape(img, seg(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], r), body, OUT, 1.3)
    ex, ey = pts[-1]
    shape(img, poly([(ex - 3 * k, ey - 4 * k), (ex + 9 * k, ey + 5 * k), (ex - 2 * k, ey + 6 * k)]), accent, OUT, 1.2)
    return img, (3, 4)


def d_flame(k, c):
    W, H = int(30 * k), int(40 * k)
    img = Img(W, H)
    cx = W / 2
    outer = poly([(cx - 9 * k, H - 6 * k), (cx - 11 * k, H * 0.55), (cx - 3 * k, H * 0.3), (cx, 2), (cx + 3 * k, H * 0.3), (cx + 11 * k, H * 0.55), (cx + 9 * k, H - 6 * k)])
    base = c["accent"] if c["crest"] >= 3 else "#ff8a2a"
    fill(img, union(outer, circle(cx, H - 11 * k, 10 * k)), vgrad(rgb(base), (255, 70, 30, 255), 0, H), ss=3)
    fill(img, union(poly([(cx - 5 * k, H - 8 * k), (cx, H * 0.38), (cx + 5 * k, H - 8 * k)]), circle(cx, H - 10 * k, 6 * k)), vgrad((255, 250, 190, 255), (255, 214, 80, 255), 0, H), ss=3)
    return img, (cx, H - 6 * k)


def d_aura(k, c):
    s = int(120 * k)
    img = Img(s, s)
    col = c["aura"]
    fill(img, circle(s / 2, s / 2, s / 2), radial(s / 2, s / 2, s / 2, (col[0], col[1], col[2], 120), (col[0], col[1], col[2], 0)), ss=1)
    return img, (s / 2, s / 2)


def dragon_parts(c):
    k = c["k"]
    wk = c["wing_k"]
    parts = []
    if c["aura"]:
        img, pv = d_aura(k, c)
        parts.append(Part("aura", img, pv, (0, 0 * k)))
    img, pv = d_tail(k, c)
    parts.append(Part("tail", img, pv, (6 * k, 18 * k)))
    img, pv = d_wing(wk * k, c, -1)
    parts.append(Part("wing_l", img, pv, (-17 * k, -8 * k)))
    img, pv = d_wing(wk * k, c, 1)
    parts.append(Part("wing_r", img, pv, (17 * k, -8 * k)))
    img, pv = d_foot(k, c)
    parts.append(Part("foot_l", img, pv, (-13 * k, 29 * k)))
    parts.append(Part("foot_r", img, pv, (13 * k, 29 * k)))
    img, pv = d_body(k, c)
    parts.append(Part("body", img, pv, (0, 6 * k)))
    img, pv = d_head(k, c)
    parts.append(Part("head", img, pv, (0, -15 * k)))
    img, pv = d_flame(k, c)
    parts.append(Part("flame", img, pv, (0, -42 * k)))
    return parts


def lerp_keys(f, keys):
    """Piecewise-linear value at frame f of [(frame, value), ...]."""
    if f <= keys[0][0]:
        return keys[0][1]
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f <= f1:
            return v0 + (v1 - v0) * (f - f0) / (f1 - f0)
    return keys[-1][1]


def sway(t, f=1, ph=0.0):
    return math.sin(2 * math.pi * (t * f + ph))


def dragon_motion(c):
    """-> {animation: (length, fps, key_frames, fn(bone, frame) -> (dx, dy, rot, sx, sy))}"""
    k = c["k"]
    idle_len = 24

    def idle(b, f):
        t = f / idle_len
        bob = 1.3 * k * sway(t)
        if b == "body":
            return 0, bob, 0, 1 - 0.012 * sway(t), 1 + 0.014 * sway(t)
        if b == "head":
            return 0, bob * 1.2, 3.2 * sway(t, 1, 0.1), 1, 1
        if b == "wing_l":
            return 0, bob * 0.6, 9 * sway(t, 1, 0.2) + 4, 1, 1
        if b == "wing_r":
            return 0, bob * 0.6, -9 * sway(t, 1, 0.2) - 4, 1, 1
        if b == "tail":
            return 0, bob * 0.3, 11 * sway(t, 1, -0.15), 1, 1
        if b == "aura":
            return 0, 0, 0, 1 + 0.07 * sway(t), 1 + 0.07 * sway(t)
        if b == "flame":
            return 0, bob, 0, 0, 0
        return 0, 0, 0, 1, 1

    def attack(b, f):
        if b == "head":
            return 0, lerp_keys(f, [(0, 0), (3, 5 * k), (5, -7 * k), (8, -2 * k), (12, 0)]), 0, lerp_keys(f, [(0, 1), (3, 0.93), (5, 1.15), (8, 1.04), (12, 1)]), lerp_keys(f, [(0, 1), (3, 0.93), (5, 1.15), (8, 1.04), (12, 1)])
        if b == "body":
            return 0, lerp_keys(f, [(0, 0), (3, 2 * k), (5, -2 * k), (12, 0)]), 0, 1, lerp_keys(f, [(0, 1), (3, 0.95), (5, 1.06), (12, 1)])
        if b in ("wing_l", "wing_r"):
            s = 1 if b == "wing_l" else -1
            return 0, 0, s * lerp_keys(f, [(0, 4), (3, 26), (5, -14), (8, 8), (12, 4)]), 1, 1
        if b == "tail":
            return 0, 0, lerp_keys(f, [(0, 0), (4, 16), (8, -10), (12, 0)]), 1, 1
        if b == "flame":
            s = lerp_keys(f, [(0, 0), (4, 0), (5, 0.9), (7, 1.15), (10, 0.5), (12, 0)])
            return 0, lerp_keys(f, [(0, 0), (4, 2 * k), (7, -9 * k), (12, -20 * k)]), 0, s, s
        if b == "aura":
            return 0, 0, 0, 1.1, 1.1
        return 0, 0, 0, 1, 1

    return {
        "idle": (idle_len, 12, list(range(0, idle_len + 1, 2)), idle),
        "attack": (12, 24, list(range(0, 13)), attack),
    }


# ---------------------------------------------------------------- enemies

ENEMIES = {
    "goblin": dict(k=1.0, skin="#6fb23a", cloth="#a0622d", scale=0.78),
    "imp": dict(k=0.84, skin="#a86bd8", cloth="#5b3b8c", scale=0.78),
    "orc": dict(k=1.28, skin="#7a9a4a", cloth="#5f6874", scale=0.8),
    "demon": dict(k=1.7, skin="#d23a3a", cloth="#3d2a45", scale=0.8),
}


def limb(w, h, k, color, tip, tip_r=0.0, shoe=None):
    W, H = int(w * k) + 4, int(h * k) + 4
    img = Img(W, H)
    cx = W / 2
    r = w * k / 2
    shape(img, seg(cx, 2 + r, cx, H - 2 - r - (3 * k if shoe else 0), r), color, OUT, 1.3)
    if tip_r:
        shape(img, circle(cx, H - 2 - tip_r * k - 0.5, tip_r * k), tip, OUT, 1.2)
    if shoe:
        shape(img, rbox(cx, H - 3.5 * k, r + 2.2 * k, 2.6 * k, 2), shoe, OUT, 1.2)
    return img, (W / 2, 2 + r)


def e_body(w, h, k, cloth, belt, trim=None, armor=None):
    W, H = int(w * k) + 6, int(h * k) + 6
    img = Img(W, H)
    cx, cy = W / 2, H / 2
    shape(img, rbox(cx, cy, w * k / 2, h * k / 2, 6 * k), cloth, OUT, 1.5)
    fill(img, rbox(cx, cy - h * k * 0.25, w * k * 0.4, h * k * 0.18, 3), (255, 255, 255, 40), ss=2)
    if armor:
        shape(img, rbox(cx, cy - h * k * 0.08, w * k * 0.44, h * k * 0.36, 4 * k), armor, OUT, 1.3)
        for dx in (-0.25, 0.25):
            fill(img, circle(cx + dx * w * k, cy - h * k * 0.08, 1.7 * k), rgb("#e8edf3"), ss=2)
    shape(img, rbox(cx, cy + h * k * 0.3, w * k / 2 - 0.5, 2.4 * k, 1), belt, OUT, 1)
    shape(img, rbox(cx, cy + h * k * 0.3, 2.4 * k, 2.2 * k, 1), trim or rgb("#f6c945"), OUT, 0.8)
    return img, (cx, cy)


def e_head(kind, k, skin, accent):
    W, H = int(60 * k), int(46 * k)
    img = Img(W, H)
    cx = W / 2
    hr = 12.5 * k
    hy = H - 5 - hr
    pivot = (cx, H - 5 * k)
    skin_d = shade(skin, -0.25)
    horn = rgb("#f1e3b8")
    if kind in ("goblin", "imp"):
        ex = 12 if kind == "goblin" else 8
        for s in (-1, 1):
            shape(img, poly([(cx + s * (hr - 2 * k), hy - 6 * k), (cx + s * (hr + ex * k), hy - 8 * k), (cx + s * (hr - 2 * k), hy + 3 * k)]), skin_d, OUT, 1.2)
    if kind == "imp":
        for s in (-1, 1):
            shape(img, poly([(cx + s * 5 * k - 2.4 * k, hy - hr + 2 * k), (cx + s * 8 * k, hy - hr - 9 * k), (cx + s * 5 * k + 2.4 * k, hy - hr + 2 * k)]), horn, OUT, 1.1)
    if kind == "demon":
        for s in (-1, 1):
            shape(img, poly([(cx + s * (hr - 8 * k), hy - hr + 4 * k), (cx + s * (hr + 5 * k), hy - hr - 3 * k), (cx + s * (hr + 2 * k), hy - hr - 15 * k), (cx + s * (hr - 4 * k), hy - hr - 2 * k), (cx + s * (hr - 11 * k), hy - hr + 7 * k)]), horn, OUT, 1.3)
    shape(img, circle(cx, hy, hr), skin, OUT, 1.5)
    fill(img, ellipse(cx - 3 * k, hy - 7 * k, 6 * k, 3 * k), (255, 255, 255, 60), ss=2)
    if kind == "orc":
        shape(img, poly([(cx - hr - 1, hy - 1 * k), (cx - hr + 1, hy - hr - 1 * k), (cx + hr - 1, hy - hr - 1 * k), (cx + hr + 1, hy - 1 * k), (cx, hy - 5 * k)]), rgb("#8d97a5"), OUT, 1.4)
        for s in (-1, 1):
            shape(img, poly([(cx + s * (hr - 1), hy - hr + 3 * k), (cx + s * (hr + 9 * k), hy - hr - 8 * k), (cx + s * (hr - 6 * k), hy - hr - 1 * k)]), horn, OUT, 1.2)
    eye_r = (3.2 if kind == "imp" else 2.9) * k
    for s in (-1, 1):
        ex, ey = cx + s * 5.4 * k, hy - 0.5 * k
        shape(img, circle(ex, ey, eye_r), accent if kind == "demon" else rgb("#ffffff"), OUT, 0.9)
        fill(img, circle(ex, ey + 0.4 * k, 1.5 * k), OUT if kind != "demon" else rgb("#ffe066"), ss=2)
        fill(img, seg(ex + s * 5 * k, ey - 6 * k, ex - s * 3 * k, ey - 3.4 * k, 1.1 * k), OUT, ss=2)
    fill(img, seg(cx - 5 * k, hy + 6.5 * k, cx + 5 * k, hy + 6.5 * k, 1.2 * k), OUT, ss=2)
    for tx in (cx - 3 * k, cx + 3 * k):
        fill(img, poly([(tx - 1.3 * k, hy + 6.4 * k), (tx + 1.3 * k, hy + 6.4 * k), (tx, hy + 9.6 * k)]), rgb("#fdfdf4"), ss=2)
    if kind == "orc":
        for s in (-1, 1):
            shape(img, poly([(cx + s * 7 * k - 1.6 * k, hy + 6 * k), (cx + s * 7 * k + 1.6 * k, hy + 6 * k), (cx + s * 7 * k, hy + 12 * k)]), horn, OUT, 0.8)
    return img, pivot


def e_wing(k, color):
    W, H = int(30 * k), int(26 * k)
    img = Img(W, H)
    base = (W - 3, H - 4)
    pts = [base, (W * 0.85, H * 0.15), (W * 0.5, H * 0.35), (W * 0.38, 2), (2, H * 0.55), (W * 0.35, H - 3)]
    shape(img, poly(pts), color, OUT, 1.3)
    return img, base


def enemy_parts(kind):
    sp = ENEMIES[kind]
    k = sp["k"]
    skin, cloth = rgb(sp["skin"]), rgb(sp["cloth"])
    skin_d = shade(skin, -0.22)
    boots = rgb("#4a2f1c")
    parts = []
    bw, bh = 24, 22
    belt = rgb("#5b3a1c")
    armor = rgb("#9aa4b2") if kind == "orc" else None
    trim = rgb("#e6c34a") if kind == "demon" else None
    hip_y = bh * k * 0.5 - 2 * k
    sh_y = -bh * k * 0.5 + 6 * k
    if kind == "imp":
        img, pv = e_wing(k * 1.5, rgb("#7a4cb4"))
        parts.append(Part("wing_l", img, pv, (-bw * k * 0.3, sh_y)))
        img, pv = e_wing(k * 1.5, rgb("#7a4cb4"))
        # mirrored copy: the right wing is drawn flipped
        flip = Img(img.w, img.h)
        for y in range(img.h):
            for x in range(img.w):
                for ch in range(4):
                    flip.px[(y * img.w + x) * 4 + ch] = img.px[(y * img.w + (img.w - 1 - x)) * 4 + ch]
        parts.append(Part("wing_r", flip, (img.w - pv[0], pv[1]), (bw * k * 0.3, sh_y)))
    img, pv = limb(7, 16, k, skin_d, skin_d, shoe=boots)
    parts.append(Part("leg_b", img, pv, (-5 * k, hip_y)))
    img, pv = limb(7, 16, k, skin, skin, shoe=boots)
    parts.append(Part("leg_f", img, pv, (5 * k, hip_y)))
    img, pv = limb(6.5, 17, k, skin_d, skin_d, tip_r=3.2)
    parts.append(Part("arm_b", img, pv, (-bw * k * 0.5, sh_y)))
    img, pv = e_body(bw, bh, k, cloth, belt, trim, armor)
    parts.append(Part("body", img, pv, (0, 0)))
    img, pv = e_head(kind, k, skin, rgb("#ffe066") if kind == "demon" else rgb("#ffffff"))
    parts.append(Part("head", img, pv, (0, sh_y + 1 * k)))
    img, pv = limb(6.5, 17, k, skin, skin, tip_r=3.2)
    parts.append(Part("arm_f", img, pv, (bw * k * 0.5, sh_y)))
    if kind == "demon":
        W, H = int(60 * k * 0.5), int(18 * k)
        sp_img = Img(W, H)
        for s in (-1, 1):
            c = W / 2 + s * W * 0.34
            shape(sp_img, poly([(c - 5 * k, H - 3), (c, 2), (c + 5 * k, H - 3)]), rgb("#e8e0cf"), OUT, 1.2)
        parts.append(Part("spikes", sp_img, (W / 2, H - 2), (0, sh_y + 3 * k), "body"))
    return parts


def enemy_motion(kind):
    k = ENEMIES[kind]["k"]
    walk_len = 8

    def walk(b, f):
        t = f / walk_len
        bob = -1.6 * k * abs(sway(t))
        if b == "leg_f":
            return 0, bob, 30 * sway(t), 1, 1
        if b == "leg_b":
            return 0, bob, -30 * sway(t), 1, 1
        if b == "arm_f":
            return 0, bob, -26 * sway(t), 1, 1
        if b == "arm_b":
            return 0, bob, 26 * sway(t), 1, 1
        if b == "head":
            return 0, bob + 0.5 * k * sway(t, 2), 3 * sway(t), 1, 1
        if b == "wing_l":
            return 0, bob, 14 + 24 * sway(t, 2), 1, 1
        if b == "wing_r":
            return 0, bob, -14 - 24 * sway(t, 2), 1, 1
        return 0, bob, 0, 1, 1

    die_keys = [(0, 0), (3, -22), (6, -62), (9, -88)]

    def die(b, f):
        g = lerp_keys(f, die_keys)
        s = lerp_keys(f, [(0, 1.0), (3, 1.06), (6, 0.8), (9, 0.35)])
        gy = lerp_keys(f, [(0, 0), (3, -3 * k), (6, 6 * k), (9, 14 * k)])
        return ("global", g, gy, s)

    return {
        "walk": (walk_len, 12, list(range(0, walk_len + 1)), walk),
        "die": (9, 15, [0, 3, 6, 9], die),
    }


# ---------------------------------------------------------------- packing / writing

def pack(parts):
    pad = 2
    order = sorted(parts, key=lambda p: -p.img.h)
    width = 256
    x = y = row_h = 0
    placed = {}
    for p in order:
        if x + p.img.w + pad > width:
            x, y, row_h = 0, y + row_h + pad, 0
        placed[p.name] = (x, y)
        x += p.img.w + pad
        row_h = max(row_h, p.img.h)
    height = y + row_h + pad
    page = Img(width, height)
    for p in order:
        px, py = placed[p.name]
        page.paste(p.img, px, py)
    return page, placed


def build(name, parts, motion):
    page, placed = pack(parts)
    bones, slots, seen = [], [], []
    for p in parts:
        if p.bone not in seen:
            seen.append(p.bone)
            bones.append({"name": p.bone, "x": p.pos[0], "y": p.pos[1], "rotation": 0, "scaleX": 1, "scaleY": 1})
        slots.append({
            "id": "slot-" + p.name, "name": p.name, "bone": p.bone,
            "attachments": [{
                "path": f"{name}/{p.name}.png",
                "size": {"width": p.img.w, "height": p.img.h},
                "x": -p.pivot[0], "y": p.img.h / 2 - p.pivot[1],
                "scaleX": 1, "scaleY": 1, "rotation": 0,
            }],
            "displayIndex": 0,
        })
    rest = {b["name"]: (b["x"], b["y"]) for b in bones}

    def pose(bone, d):
        x, y = rest[bone]
        if d[0] == "global":  # whole-body transform (falling over): rotate + scale around the origin, then move
            _, gr, gy, gs = d
            c, s = math.cos(math.radians(gr)), math.sin(math.radians(gr))
            px, py = x, y
            px, py = (px * c - py * s) * gs, (px * s + py * c) * gs + gy
            return {"x": round(px, 3), "y": round(py, 3), "rotation": round(gr, 3), "scaleX": round(gs, 4), "scaleY": round(gs, 4)}
        dx, dy, rot, sx, sy = d
        return {"x": round(x + dx, 3), "y": round(y + dy, 3), "rotation": round(rot, 3), "scaleX": round(sx, 4), "scaleY": round(sy, 4)}

    animations = {}
    for aname, (length, fps, key_frames, fn) in motion.items():
        kf = {b["name"]: {} for b in bones}
        for f in key_frames:
            for b in bones:
                kf[b["name"]][str(f)] = pose(b["name"], fn(b["name"], f))
        animations[aname] = {"name": aname, "length": length, "fps": fps, "keyframes": kf}

    skel = {
        "canvasSize": {"width": 100, "height": 180},
        "bones": bones,
        "slots": slots,
        "skins": [{"id": "default", "name": "Default", "attachments": {}}],
        "activeSkinId": "default",
        "physicsConstraints": [], "transformConstraints": [], "ikConstraints": [],
        "animations": animations,
    }
    atlas = {
        "image": f"{name}.png", "width": page.w, "height": page.h,
        "regions": [
            {"path": f"{name}/{p.name}.png", "x": placed[p.name][0], "y": placed[p.name][1], "width": p.img.w, "height": p.img.h}
            for p in parts
        ],
    }
    return skel, atlas, page


def all_rigs():
    """-> [(file name, parts, motion)]"""
    out = []
    for i, c in enumerate(DRAGONS):
        out.append((f"dragon{i + 1}", dragon_parts(c), dragon_motion(c)))
    for kind in ENEMIES:
        out.append((kind, enemy_parts(kind), enemy_motion(kind)))
    return out
