# Comfy CUDA Wheels

Pre-built CUDA Python wheels for packages used by ComfyUI custom nodes. Spec-driven build pipeline consuming `packages/*.yml` configurations.

## Packages

| Package | Source |
|:--|:--|
| flash_attn | [Dao-AILab/flash-attention](https://github.com/Dao-AILab/flash-attention) |
| sageattn | [thu-ml/SageAttention](https://github.com/thu-ml/SageAttention) |
| sageattn3 | [thu-ml/SageAttention](https://github.com/thu-ml/SageAttention) |
| cc_torch | [ronghanghu/cc_torch](https://github.com/ronghanghu/cc_torch) |
| torch_generic_nms | [ronghanghu/torch_generic_nms](https://github.com/ronghanghu/torch_generic_nms) |
| triton | [triton-lang/triton](https://github.com/triton-lang/triton) |

## Building a wheel

1. Ensure a package spec exists in `packages/<name>.yml`
2. Run: `gh workflow run build.yml --repo pollockjj/wheels -f package=<name>`
3. Download the wheel from the GitHub release

## Package index

Wheels are served via PEP 503 index at the GitHub Pages URL for this repository.

## Adding a package

Create `packages/<name>.yml` with required fields: `name`, `source_repo`, `version`, `build_matrix`. See existing specs for format.

## Attribution

See [ATTRIBUTION.md](ATTRIBUTION.md) for upstream source credits.
