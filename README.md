# Comfy CUDA Wheels

Pre-built CUDA Python wheels for packages used by ComfyUI custom nodes. Spec-driven build pipeline consuming `packages/*.yml` configurations.

## Packages

| Package | Source | Pinned Ref | Custom Nodes |
|:--|:--|:--|:--|
| cc_torch | [ronghanghu/cc_torch](https://github.com/ronghanghu/cc_torch) | [`446e936`](https://github.com/ronghanghu/cc_torch/commit/446e9360ed10d3c8d03925ccb5f220ccb62009de) | [pollockjj/ComfyUI-SAM3](https://github.com/pollockjj/ComfyUI-SAM3) |
| flash_attn | [Dao-AILab/flash-attention](https://github.com/Dao-AILab/flash-attention) | [`v2.8.3`](https://github.com/Dao-AILab/flash-attention/releases/tag/v2.8.3) | [pollockjj/ComfyUI-SAM3](https://github.com/pollockjj/ComfyUI-SAM3) |
| sageattention | [thu-ml/SageAttention](https://github.com/thu-ml/SageAttention) | [`v2.2.0`](https://github.com/thu-ml/SageAttention/releases/tag/v2.2.0) | |
| sageattn3 | [thu-ml/SageAttention](https://github.com/thu-ml/SageAttention) | [`v2.2.0`](https://github.com/thu-ml/SageAttention/releases/tag/v2.2.0) | |
| torch_generic_nms | [ronghanghu/torch_generic_nms](https://github.com/ronghanghu/torch_generic_nms) | [`fcf02b4`](https://github.com/ronghanghu/torch_generic_nms/commit/fcf02b41ea9b37988b244ef80583af17baa4a7f0) | [pollockjj/ComfyUI-SAM3](https://github.com/pollockjj/ComfyUI-SAM3) |

## Building a wheel

1. Ensure a package spec exists in `packages/<name>.yml`
2. Run: `gh workflow run build.yml --repo <owner>/wheels -f package=<name>`
3. Download the wheel from the GitHub release

## Package index

Wheels are served via PEP 503 index at the GitHub Pages URL for this repository.

## Adding a package

Create `packages/<name>.yml` with required fields: `name`, `source_repo`, `version`, `build_matrix`. See existing specs for format.

## Attribution

See [ATTRIBUTION.md](ATTRIBUTION.md) for upstream source credits.
