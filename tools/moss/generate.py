#!/usr/bin/env python3
"""Renders art_raw/<name>_<seed>.png for every entry in manifest.py with MOSS-Image-SFT 8-step DMD (MLX).

    uv run --no-project --python 3.12 --with moss-image-mlx --with "huggingface_hub" python tools/moss/generate.py --only dragon1 --seeds 1,2
    ... generate.py --list            # names and prompts, nothing rendered
    ... generate.py --skip-existing   # resume

First run downloads ~15 GB (8-bit MLX base + the DMD adapter). Each image takes one network evaluation per step (8).
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import manifest  # noqa: E402

RAW = os.path.join(HERE, "..", "..", "art_raw")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--only", default="", help="comma-separated name prefixes")
    p.add_argument("--seeds", default="1", help="comma-separated seeds, one image each")
    p.add_argument("--steps", type=int, default=8)
    p.add_argument("--skip-existing", action="store_true")
    p.add_argument("--list", action="store_true")
    a = p.parse_args()

    only = [s for s in a.only.split(",") if s]
    items = [i for i in manifest.ITEMS if not only or any(i.name.startswith(o) for o in only)]
    jobs = [(i, int(s)) for i in items for s in a.seeds.split(",")]
    jobs = [(i, s) for i, s in jobs if not (a.skip_existing and os.path.exists(f"{RAW}/{i.name}_{s}.png"))]
    if a.list:
        for i, s in jobs:
            print(f"{i.name}_{s}  {i.width}x{i.height}  {i.prompt}")
        return

    from dmd import DmdPipeline, Req
    from PIL import Image

    os.makedirs(RAW, exist_ok=True)
    pipe = DmdPipeline()
    reqs = [Req(prompt=i.prompt, width=i.width, height=i.height, seed=s, steps=a.steps) for i, s in jobs]
    names = [f"{i.name}_{s}" for i, s in jobs]
    t0 = time.perf_counter()
    for n, (req, image, secs) in enumerate(pipe.generate_many(reqs)):
        path = f"{RAW}/{names[n]}.png"
        Image.fromarray(image).save(path)
        print(f"[{n + 1}/{len(reqs)}] {path}  {secs:.0f}s", flush=True)
    print(f"done in {time.perf_counter() - t0:.0f}s")


if __name__ == "__main__":
    main()
