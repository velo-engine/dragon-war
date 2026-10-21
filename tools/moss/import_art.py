#!/usr/bin/env python3
"""art_raw/<name>_<seed>.png -> assets/characters/<name>.{png,skel.json,atlas.json}

Each character becomes ONE weighted Kine2D mesh (a grid over the cut-out) skinned to a few bones, so the whole
picture bends: dragons (body, head, wing_l, wing_r, tail) get `idle` + `attack`; enemies (body, head, arm_l, arm_r,
leg_l, leg_r) get `walk` + `die`. Asset paths and animation names match the old procedural rigs, so no code or scene
changes. The picture is placed inside the old rig's bounding box (the numbers in BOX) at 2x texture resolution.

    uv run --no-project --python 3.12 --with pillow --with numpy --with scipy --with rembg --with onnxruntime \
        python tools/moss/import_art.py [--only dragon1,goblin] [--pick dragon1=2]
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
RAW, OUT = os.path.join(ROOT, "art_raw"), os.path.join(ROOT, "assets", "characters")

# (max width, max height, bottom y) in canvas px, from the old rigs
BOX = {
    "dragon1": (90, 104, 36), "dragon2": (98, 111, 36), "dragon3": (106, 120, 36), "dragon4": (116, 128, 36),
    "dragon5": (124, 134, 36), "dragon6": (134, 140, 36),
    "goblin": (60, 69, 24), "imp": (80, 57, 20), "orc": (76, 86, 29), "demon": (102, 114, 38),
}
SCALE = 0.5  # attachment scale: the texture is 2x the canvas pixels
GRID = (14, 18)  # mesh cells (columns, rows)

PIVOTS = {  # bone -> (u, v) of its pivot in the picture
    "dragon": {"body": (.5, .62), "head": (.5, .42), "wing_l": (.30, .55), "wing_r": (.70, .55), "tail": (.65, .80)},
    "enemy": {"body": (.5, .6), "head": (.5, .32), "arm_l": (.22, .45), "arm_r": (.78, .45),
              "leg_l": (.40, .72), "leg_r": (.60, .72)},
}


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def weights(kind, u, v):
    """-> {bone: weight array}, summing to 1."""
    left = u < .5
    if kind == "dragon":
        ww = smooth((np.abs(u - .5) - .24) / .12) * smooth((.80 - v) / .08)
        wh = (1 - ww) * smooth((.46 - v) / .10)
        wt = (1 - ww) * (1 - wh) * smooth((u - .60) / .10) * smooth((v - .70) / .08)
        wb = 1 - ww - wh - wt
        return {"body": wb, "head": wh, "tail": wt, "wing_l": ww * left, "wing_r": ww * ~left}
    wa = smooth((np.abs(u - .5) - .26) / .10) * smooth((v - .30) / .08) * smooth((.78 - v) / .08)
    wh = (1 - wa) * smooth((.38 - v) / .08)
    wl = (1 - wa) * (1 - wh) * smooth((v - .70) / .08)
    wb = 1 - wa - wh - wl
    return {"body": wb, "head": wh, "arm_l": wa * left, "arm_r": wa * ~left, "leg_l": wl * left, "leg_r": wl * ~left}


# ---------------------------------------------------------------- cut-out

_session = None


def cutout(path):
    global _session
    from rembg import new_session, remove

    _session = _session or new_session("isnet-anime")
    src = Image.open(path).convert("RGB")
    out = np.array(remove(src, session=_session).convert("RGBA")).astype(np.float32)
    a = out[..., 3:] / 255
    # defringe: un-mix the white background from semi-transparent edge pixels
    rgb = np.where(a > .02, (out[..., :3] - 255 * (1 - a)) / np.maximum(a, .02), out[..., :3])
    out[..., :3] = np.clip(rgb, 0, 255)
    out[..., 3] = np.where(out[..., 3] < 8, 0, out[..., 3])
    img = Image.fromarray(out.astype(np.uint8), "RGBA")
    return img.crop(img.getchannel("A").getbbox())


# ---------------------------------------------------------------- mesh + rig

def make_mesh(img, kind):
    """Grid mesh over the picture, only cells that touch the picture; vertices skinned by `weights`."""
    w, h = img.size
    cols, rows = GRID
    alpha = np.array(img.getchannel("A")) > 8
    keep = np.zeros((rows, cols), bool)
    for r in range(rows):
        for c in range(cols):
            y0, y1 = r * h // rows, (r + 1) * h // rows
            x0, x1 = c * w // cols, (c + 1) * w // cols
            keep[r, c] = alpha[y0:y1, x0:x1].any()
    pad = keep.copy()  # one cell of margin so the soft edge never gets clipped
    pad[1:] |= keep[:-1]; pad[:-1] |= keep[1:]; pad[:, 1:] |= keep[:, :-1]; pad[:, :-1] |= keep[:, 1:]
    index, verts, uvs, tris = {}, [], [], []

    def vid(r, c):
        if (r, c) not in index:
            index[(r, c)] = len(verts) // 2
            u, v = c / cols, r / rows
            verts.extend([round(u * w, 2), round(v * h - h / 2, 2)])
            uvs.extend([round(u, 5), round(v, 5)])
        return index[(r, c)]

    for r in range(rows):
        for c in range(cols):
            if pad[r, c]:
                a, b, d, e = vid(r, c), vid(r, c + 1), vid(r + 1, c + 1), vid(r + 1, c)
                tris += [a, b, d, a, d, e]
    uv = np.array(uvs).reshape(-1, 2)
    ws = weights(kind, uv[:, 0], uv[:, 1])
    bones = list(ws)
    vw = []
    for i in range(len(uv)):
        d = {b: round(float(ws[b][i]), 4) for b in bones if ws[b][i] > 1e-3}
        vw.append(d or {"body": 1.0})
    return {"vertices": verts, "uvs": uvs, "triangles": tris, "weights": vw, "width": w, "height": h}


def lerp_keys(f, keys):
    if f <= keys[0][0]:
        return keys[0][1]
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f <= f1:
            return v0 + (v1 - v0) * (f - f0) / (f1 - f0)
    return keys[-1][1]


def sway(t, f=1, ph=0.0):
    return math.sin(2 * math.pi * (t * f + ph))


def dragon_motion():
    n = 24

    def idle(b, f):
        t = f / n
        bob = 1.3 * sway(t)
        return {
            "body": (0, bob, 0, 1 - .012 * sway(t), 1 + .014 * sway(t)),
            "head": (0, bob * 1.2, 3.2 * sway(t, 1, .1), 1, 1),
            "wing_l": (0, bob * .6, 9 * sway(t, 1, .2) + 4, 1, 1),
            "wing_r": (0, bob * .6, -9 * sway(t, 1, .2) - 4, 1, 1),
            "tail": (0, bob * .3, 11 * sway(t, 1, -.15), 1, 1),
        }[b]

    def attack(b, f):
        if b == "head":
            s = lerp_keys(f, [(0, 1), (3, .95), (5, 1.12), (8, 1.04), (12, 1)])
            return 0, lerp_keys(f, [(0, 0), (3, 4), (5, -6), (8, -2), (12, 0)]), 0, s, s
        if b == "body":
            return 0, lerp_keys(f, [(0, 0), (3, 2), (5, -2), (12, 0)]), 0, 1, lerp_keys(f, [(0, 1), (3, .95), (5, 1.06), (12, 1)])
        if b in ("wing_l", "wing_r"):
            s = 1 if b == "wing_l" else -1
            return 0, 0, s * lerp_keys(f, [(0, 4), (3, 26), (5, -14), (8, 8), (12, 4)]), 1, 1
        return 0, 0, lerp_keys(f, [(0, 0), (4, 16), (8, -10), (12, 0)]), 1, 1  # tail

    return {"idle": (n, 12, list(range(0, n + 1, 2)), idle), "attack": (12, 24, list(range(13)), attack)}


def enemy_motion():
    n = 8

    def walk(b, f):
        t = f / n
        bob = -1.8 * abs(sway(t))
        return {
            "body": (0, bob, 3 * sway(t), 1, 1 + .015 * abs(sway(t))),
            "head": (0, bob + .6 * sway(t, 2), -3 * sway(t), 1, 1),
            "leg_l": (0, bob, 16 * sway(t), 1, 1), "leg_r": (0, bob, -16 * sway(t), 1, 1),
            "arm_l": (0, bob, -12 * sway(t), 1, 1), "arm_r": (0, bob, 12 * sway(t), 1, 1),
        }[b]

    def die(b, f):
        g = lerp_keys(f, [(0, 0), (3, -22), (6, -62), (9, -88)])
        s = lerp_keys(f, [(0, 1.0), (3, 1.06), (6, .8), (9, .35)])
        gy = lerp_keys(f, [(0, 0), (3, -3), (6, 6), (9, 14)])
        return ("global", g, gy, s)

    return {"walk": (n, 12, list(range(n + 1)), walk), "die": (9, 15, [0, 3, 6, 9], die)}


def build(name, img, kind):
    bw, bh, bottom = BOX[name]
    fit = min(bw / img.width, bh / img.height)
    tex_scale = 2 * fit  # texture px per source px
    img = img.resize((round(img.width * tex_scale), round(img.height * tex_scale)), Image.LANCZOS)
    w, h = img.size
    cw, ch = w * SCALE, h * SCALE  # size on the canvas
    cy = bottom - ch / 2
    bones = {b: (round((u - .5) * cw, 2), round(cy + (v - .5) * ch, 2)) for b, (u, v) in PIVOTS[kind].items()}
    mesh = make_mesh(img, kind)
    body = bones["body"]
    skel_bones = [{"name": b, "x": x, "y": y, "rotation": 0, "scaleX": 1, "scaleY": 1} for b, (x, y) in bones.items()]
    slot = {"id": "slot-body", "name": "body", "bone": "body", "attachments": [{
        "path": f"{name}/body.png", "size": {"width": w, "height": h},
        "x": round(-cw / 2 - body[0], 2), "y": round(cy - body[1], 2), "scaleX": SCALE, "scaleY": SCALE, "rotation": 0,
        "mesh": mesh}], "displayIndex": 0}

    def pose(bone, d):
        x, y = bones[bone]
        if d[0] == "global":  # whole-body fall: rotate + scale about the canvas origin, then move
            _, gr, gy, gs = d
            c, s = math.cos(math.radians(gr)), math.sin(math.radians(gr))
            return {"x": round((x * c - y * s) * gs, 3), "y": round((x * s + y * c) * gs + gy, 3), "rotation": round(gr, 3),
                    "scaleX": round(gs, 4), "scaleY": round(gs, 4)}
        dx, dy, rot, sx, sy = d
        return {"x": round(x + dx, 3), "y": round(y + dy, 3), "rotation": round(rot, 3), "scaleX": round(sx, 4), "scaleY": round(sy, 4)}

    anims = {}
    for an, (length, fps, frames, fn) in (dragon_motion() if kind == "dragon" else enemy_motion()).items():
        anims[an] = {"name": an, "length": length, "fps": fps,
                     "keyframes": {b: {str(f): pose(b, fn(b, f)) for f in frames} for b in bones}}
    skel = {"canvasSize": {"width": 100, "height": 180}, "bones": skel_bones, "slots": [slot],
            "skins": [{"id": "default", "name": "Default", "attachments": {}}], "activeSkinId": "default",
            "physicsConstraints": [], "transformConstraints": [], "ikConstraints": [], "animations": anims}
    atlas = {"image": f"{name}.png", "width": w, "height": h,
             "regions": [{"path": f"{name}/body.png", "x": 0, "y": 0, "width": w, "height": h}]}
    return skel, atlas, img


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--only", default="")
    p.add_argument("--pick", default="", help="name=seed,... (default seed 1)")
    a = p.parse_args()
    pick = dict(kv.split("=") for kv in a.pick.split(",") if kv)
    only = [s for s in a.only.split(",") if s]
    for name in BOX:
        if only and name not in only:
            continue
        src = os.path.join(RAW, f"{name}_{pick.get(name, 1)}.png")
        if not os.path.exists(src):
            print("missing", src, file=sys.stderr)
            continue
        kind = "dragon" if name.startswith("dragon") else "enemy"
        skel, atlas, img = build(name, cutout(src), kind)
        img.save(os.path.join(OUT, f"{name}.png"))
        json.dump(skel, open(os.path.join(OUT, f"{name}.skel.json"), "w"), indent=1)
        json.dump(atlas, open(os.path.join(OUT, f"{name}.atlas.json"), "w"), indent=1)
        print(name, img.size, len(skel["slots"][0]["attachments"][0]["mesh"]["vertices"]) // 2, "verts")


if __name__ == "__main__":
    main()
