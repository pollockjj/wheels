# Attribution

This repository adapts the spec-driven CUDA wheel build pipeline from [PozzettiAndrea/cuda-wheels](https://github.com/PozzettiAndrea/cuda-wheels).

## What was adapted

- **Package spec format** (`packages/*.yml`): The YAML configuration format for defining CUDA wheel build matrices (combinations of CUDA, PyTorch, and Python versions).
- **Build pipeline** (`scripts/generate_matrix.py`, `scripts/patch_wheel_version.py`): Scripts that consume package specs and generate build matrices and wheel name suffixes.
- **Index generation** (`scripts/generate_index.py`): PEP 503 index generation from GitHub releases.

## What was NOT copied

- The entire repository structure, history, or identity
- Unrelated package specifications (we only include packages Comfy intends to serve)
- Dashboard UI, gap analysis, or install helper
- Any branding, naming, or documentation from the upstream repo

## Per-package provenance

| Package | Upstream build spec | Source repo |
|:--|:--|:--|
| flash_attn | Adapted from `PozzettiAndrea/cuda-wheels` `packages/flash_attn.yml` | [Dao-AILab/flash-attention](https://github.com/Dao-AILab/flash-attention) |
| sageattn | Adapted from `PozzettiAndrea/cuda-wheels` `packages/sageattn.yml` | [thu-ml/SageAttention](https://github.com/thu-ml/SageAttention) |
| sageattn3 | Adapted from `PozzettiAndrea/cuda-wheels` `packages/sageattn3.yml` | [thu-ml/SageAttention](https://github.com/thu-ml/SageAttention) |
| cc_torch | Adapted from `PozzettiAndrea/cuda-wheels` `packages/cc_torch.yml` | [ronghanghu/cc_torch](https://github.com/ronghanghu/cc_torch) |
| torch_generic_nms | Adapted from `PozzettiAndrea/cuda-wheels` `packages/torch_generic_nms.yml` | [ronghanghu/torch_generic_nms](https://github.com/ronghanghu/torch_generic_nms) |
| triton | Adapted from `PozzettiAndrea/cuda-wheels` `packages/triton.yml` | [triton-lang/triton](https://github.com/triton-lang/triton) |

Upstream license: MIT
