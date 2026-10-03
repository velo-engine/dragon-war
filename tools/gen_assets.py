#!/usr/bin/env python3
"""Generates every asset of the game: PNG sprites, Kine2D characters (6 dragons + 4 enemies), WAV sounds, prefabs and scenes (+ .meta files).

    python3 tools/gen_assets.py            # everything
    python3 tools/gen_assets.py art        # only sprites (art | rigs | sounds | scenes)

Pure Python, no packages needed. The output goes to assets/ and is meant to be committed.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "gen"))

import art  # noqa: E402
import rigs  # noqa: E402
import scenes  # noqa: E402
import sfx  # noqa: E402


def out(path):
    full = os.path.join(scenes.ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    return full


def sprites():
    items = [
        ("field", art.make_field, {}), ("wall", art.make_wall, {}), ("floor", art.make_floor, {}),
        ("slot", art.make_slot, {}), ("bench", art.make_bench_slot, {}), ("slot_hi", art.make_slot_hi, {}),
        ("fireball", art.make_fireball, {}), ("spark", art.make_spark, {}), ("ring", art.make_ring, {}), ("shadow", art.make_shadow, {}),
        ("icon_coin", art.make_coin, {}), ("icon_heart", art.make_heart, {}), ("icon_wave", art.make_wave, {}),
        ("icon_pause", art.make_pause, {}), ("icon_ff", art.make_ff, {}), ("icon_egg", art.make_egg, {}),
        ("menu_bg", art.make_menu_bg, {}),
    ]
    for name, fn, opts in items:
        path = f"sprites/{name}.png"
        fn().save(out(path))
        scenes.meta(path, "texture", **opts)
        print("  ", path)
    art.make_icon().save(os.path.join(HERE, "..", "icon.png"))
    print("   icon.png")


def characters():
    for name, parts, motion in rigs.all_rigs():
        skel, atlas, page = rigs.build(name, parts, motion)
        page.save(out(f"characters/{name}.png"))
        with open(out(f"characters/{name}.skel.json"), "w") as f:
            json.dump(skel, f, indent=1)
        with open(out(f"characters/{name}.atlas.json"), "w") as f:
            json.dump(atlas, f, indent=1)
        scenes.meta(f"characters/{name}.png", "texture")
        scenes.meta(f"characters/{name}.skel.json", "text")
        scenes.meta(f"characters/{name}.atlas.json", "text")
        print("  ", name)


def sounds():
    for name, samples in sfx.effects().items():
        sfx.wav_write(out(f"sounds/{name}.wav"), samples)
        scenes.meta(f"sounds/{name}.wav", "audio")
    sfx.wav_write(out("sounds/music.wav"), sfx.music(), gain=0.8)
    scenes.meta("sounds/music.wav", "audio")
    print("   sounds")


def prefabs():
    scenes.write_all_prefabs()
    print("   prefabs and scenes")


if __name__ == "__main__":
    which = sys.argv[1:] or ["art", "rigs", "sounds", "scenes"]
    if "art" in which:
        sprites()
    if "rigs" in which:
        characters()
    if "sounds" in which:
        sounds()
    if "scenes" in which:
        prefabs()
