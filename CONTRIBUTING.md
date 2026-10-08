# Contributing

## The notebook contract

Adapted from [lc-colab-workshops](https://github.com/langchain-samples/lc-colab-workshops).
`python3 tools/check_notebooks.py` enforces the mechanical rules.

1. **Cell 0 is the Colab badge**, pointing at `main` and this notebook's own path. Paths are
   permanent: badge URLs get pasted into decks and chat.
2. **Cell 1 says what you'll do**: the agent and the outcome, not the API surface.
3. **A notebook depends on nothing but PyPI.** No cloning, no `curl`, no imports from this repo.
4. **One setup cell**, identical in shape everywhere: install (Colab) or `load_dotenv()`
   (local), read `LANGSMITH_API_KEY`, resolve the participant's workspace, set a per-notebook
   `LANGSMITH_PROJECT`, define `MODEL`. It raises in the cell that is about the problem.
5. **`MODEL` is one named constant** per notebook.
6. **Teaching-relevant text is visible.** Prompts and tool docstrings live in visible cells.
7. **Bulk data goes in a Colab form cell** (`#@title ... { display-mode: "form" }`).
8. **Outputs are stripped** before commit.
9. **Only `LANGSMITH_API_KEY`**, plus the optional `LANGSMITH_GATEWAY_API_KEY`.
10. **Every notebook but `00_setup` ends with 📌 Key takeaways.**

## Repeated blocks

The setup cell exists once per notebook, wrapped in markers:

```python
# --- snippet:setup v1 ---
...
# --- /snippet ---
```

Change one, change them all: `rg -l 'snippet:setup' notebooks/`. Keep the setup cell's pins
in step with the `notebook` group in `pyproject.toml`.

## Hooks

`mise run setup` installs them (lefthook). On commit: strip notebook outputs, ruff, ty, the
notebook lint, `terraform fmt`, the secret scan and the denylist scan.

## Tests

Deferred. There is no test suite yet.
