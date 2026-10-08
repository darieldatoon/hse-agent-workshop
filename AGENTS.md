# Agent guide

## Context

This repo is the hands-on lab for a customer workshop. Read `.scratch/BRIEF.md` first if it
exists: it holds the design brief and is gitignored on purpose.

**This repo is public. Never name the customer anywhere in it**: code, data, prompts, docs,
commit messages, branch names. Never commit real attendee names or emails (they belong in the
gitignored `infra/attendees.csv`). `tools/scan_denylist.sh` blocks commits that contain a term
from the local, gitignored `.denylist`.

## Layout

| Path | What |
|---|---|
| `notebooks/` | The Colab notebooks. Follow the contract in `CONTRIBUTING.md` |
| `seed/` | `hse-seed`: generates the v0 agent's traces once, then replays them into every workspace |
| `infra/` | Terraform: one workspace per attendee, org invites, memberships, the shared key |
| `tools/` | Notebook lint, secret scan, denylist scan |

## Toolchain

- mise for tools and tasks (`mise tasks`). Install packages through `sfw` (Socket Firewall).
- uv workspace: the root is a virtual project holding the notebook stack; `seed/` is a member.
  ruff and ty check both. Python 3.12, which Colab runs.
- Terraform with the `langchain-ai/langsmith` provider. `terraform fmt` runs on commit.
- lefthook: see `lefthook.yml`.

## Tests

Deferred. There is no test suite, no pytest dependency and no test hook yet.

## Notebooks

Edit the `.ipynb` files directly. Keep every setup cell's pins equal to the `notebook` group
in `pyproject.toml`. Run `mise run check` before committing.
