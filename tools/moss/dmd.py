"""MOSS-Image-SFT 8-step data-space DMD sampler on Apple Silicon (MLX), built on moss-image-mlx.

    pipe = DmdPipeline()                       # 8-bit MLX base + lodestones/MOSS-Image-SFT-8-steps-dmd adapter
    for req, image in pipe.generate_many([Req(prompt="...", width=768, height=768, seed=1)]):
        Image.fromarray(image).save("out.png")

The adapter stays unmerged (the distillation delta is below bf16 rounding): a rank-128 LoRA on every block's
proj.{q,k,v,o,ffn_up_gate,ffn_down} run in fp32, fp32 time embedding + modulation biases, and the model's `precise`
mode (fp32 residual stream). No CFG: one network evaluation per step.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import mlx.core as mx
import mlx.nn as nn
import numpy as np
from huggingface_hub import hf_hub_download, snapshot_download
from moss_image_mlx.pipeline import MOSSImagePipeline
from moss_image_mlx.torch_randn import randn

BASE = "VisualInference/MOSS-Image-SFT-MLX-8bit"
ADAPTER = "lodestones/MOSS-Image-SFT-8-steps-dmd"


@dataclass
class Req:
    prompt: str
    width: int = 768
    height: int = 768
    seed: int = 1
    steps: int = 8  # every prefix of the 8 steps is trained, fewer also works


class LoRA(nn.Module):
    """y = W x + up(down(x)), alpha == rank so the scale is 1; the low-rank path runs in fp32."""

    def __init__(self, base, down, up):
        super().__init__()
        self.base, self.down, self.up = base, down, up

    def __call__(self, x):
        y = self.base(x)
        low = (x.astype(mx.float32) @ self.down.T) @ self.up.T
        return (y.astype(mx.float32) + low).astype(y.dtype)


def apply_adapter(model, weights: dict):
    for index, layer in enumerate(model.layers):
        for name in list(layer.proj):
            key = f"layers.{index}.proj.{name}"
            layer.proj[name] = LoRA(layer.proj[name], weights[f"{key}.lora_A"], weights[f"{key}.lora_B"])
    # fp32 replacements for the step embedder and the modulation biases (the t=1 vector is folded into them)
    model.time_embedding[0].weight = weights["time_embedding.0.weight"]
    model.time_embedding[0].bias = weights["time_embedding.0.bias"]
    model.time_embedding[1].weight = weights["time_embedding.2.weight"]
    model.time_embedding[1].bias = weights["time_embedding.2.bias"]
    model.shared_block_modulation.bias = weights["shared_block_modulation.bias"]
    model.video_head_modulation.bias = weights["video_head_modulation.bias"]


class DmdPipeline:
    def __init__(self, base: str = BASE):
        self.pipe = MOSSImagePipeline(snapshot_download(base), low_memory=True, precise=True)
        self.weights = mx.load(hf_hub_download(ADAPTER, "generator.safetensors"))
        self.Q, self.codes = self.weights["latent_mix.Q"], [float(c) for c in np.array(self.weights["step_codes"])]

    def _transformer(self):
        if self.pipe.transformer is None:
            self.pipe._load_transformer()
            apply_adapter(self.pipe.transformer, self.weights)
        return self.pipe.transformer

    def _sample(self, model, req: Req, context, on_step=None):
        z = mx.array(randn((1, 128, req.height // 16, req.width // 16), req.seed))
        x0 = mx.zeros_like(z)
        for r in range(req.steps):
            x = z + mx.einsum("oc,bchw->bohw", self.Q, x0)
            v = model(x, self.codes[r], context).astype(mx.float32)
            x0 = z - v
            mx.eval(x0)
            if on_step:
                on_step(r, req.steps)
        return x0

    def generate_many(self, requests: list[Req], on_step=None):
        if any(r.width % 16 or r.height % 16 for r in requests):
            raise ValueError("width and height must be multiples of 16")
        embeds = dict(zip([r.prompt for r in requests], self.pipe.encode([r.prompt for r in requests], 4096, keep=True)))
        self.pipe.free_text_encoder()
        for n, req in enumerate(requests):
            t0 = time.perf_counter()
            latents = self._sample(self._transformer(), req, embeds[req.prompt], on_step)
            last = n == len(requests) - 1
            if last:
                self.pipe.free_transformer()
            yield req, self.pipe.decode(latents, keep=not last), time.perf_counter() - t0
