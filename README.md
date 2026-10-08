# HSE Agent Workshop: find the bugs, then prove the fix

A hands-on LangSmith lab. An HSE (health, safety and environment) triage agent has been
classifying incident reports from field sites, and something is wrong with it. You'll read its
traces to find out what, turn what you find into a dataset and evaluators, and prove that an
improved version fixes it.

## Before you start

You need:

- A **personal Google account**, to run Colab.
- Your **LangSmith invite**, accepted. Each participant gets their own workspace.
- A **LangSmith API key** you create in your workspace. [00 · Setup](notebooks/00_setup.ipynb) shows how.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/darieldatoon/hse-agent-workshop/blob/main/notebooks/00_setup.ipynb)
**Start here → [00 · Setup](notebooks/00_setup.ipynb)**

## Notebooks

| | Notebook | What you do |
|---|---|---|
| 00 | [Setup](notebooks/00_setup.ipynb) | Check your key, a model call, and that traces land in your workspace |
| 01 | [Build the triage agent](notebooks/01_build_agent.ipynb) | Build the agent with `create_agent`, run it, read its traces |
| 02 | [The hunt](notebooks/02_hunt.ipynb) | Read a week of production traces in LangSmith and flag what's wrong |
| 03 | [Evaluate and fix](notebooks/03_evaluate_and_fix.ipynb) | Turn flagged traces into a dataset and evaluators, then compare v0 with v1 |

## Running locally

Colab is the intended environment, but the notebooks run the same way locally with
[`uv`](https://docs.astral.sh/uv/getting-started/installation/):

```bash
git clone https://github.com/darieldatoon/hse-agent-workshop
cd hse-agent-workshop
uv sync
cp .env.example .env    # then paste your API key into LANGSMITH_API_KEY
uv run jupyter lab notebooks
```

## For the instructor

[mise](https://mise.jdx.dev) pins the tools (uv, Terraform, lefthook, the LangSmith CLI and
Socket Firewall).

```bash
mise trust && mise install && mise run setup
cp .env.example .env    # an org admin key in LANGSMITH_API_KEY
```

**Workspaces** (`infra/`, Terraform with the
[LangSmith provider](https://registry.terraform.io/providers/langchain-ai/langsmith)):

```bash
cp infra/attendees.example.csv infra/attendees.csv          # real attendees; gitignored
cp infra/terraform.tfvars.example infra/terraform.tfvars    # gitignored
mise run infra:init
mise run infra:apply    # workspaces and org invites
# once invites are accepted: set add_workspace_members = true, then apply again
```

Terraform state holds attendee emails. It stays local and gitignored.

**Seeding** (`seed/`): replays a day of the v0 agent's traces into a workspace, with reporter
feedback, the `flag` feedback key and the `hse-triage-review` dataset. Re-running replaces them.

```bash
mise run seed -- upload --workspace-id <id>    # repeat the flag for several; none means the key's own
mise run seed -- key                           # the answer key, as a Markdown table
```
