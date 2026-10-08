"""`hse-seed`: replay the lab's production traces into attendee workspaces."""

import argparse
import os
import random

from langsmith import Client

from hse_workshop_seed.capture import capture
from hse_workshop_seed.fixtures import FIXTURES
from hse_workshop_seed.turns import site_named
from hse_workshop_seed.upload import upload

WRONG = {
    "photo": "the photo shows worse than the text; severity too low, not escalated",
    "site": "names a site the report never mentions",
    "escalation": "skipped the policy; should have escalated",
    "loop": "looked the site up again and again, then guessed",
}


def _upload(workspace_ids: list[str]) -> None:
    # Capture must not also trace to the instructor's own project.
    os.environ["LANGSMITH_TRACING"] = "false"
    print(f"Capturing {len(FIXTURES)} traces...")
    traces = capture()
    for workspace_id in workspace_ids or [None]:
        client = Client(workspace_id=workspace_id)
        print(f"Uploading to workspace {workspace_id or '(the key default)'}...")
        upload(client, traces, random.Random())
    print("Done.")


def _key() -> None:
    print("| # | Bug | Site v0 named | Rating | Report |")
    print("|---|---|---|---|---|")
    for i, f in enumerate(FIXTURES, 1):
        rating = {None: "", 1: "👍", 0: "👎"}[f.rating.score if f.rating else None]
        bug = f"{f.bug}: {WRONG[f.bug]}" if f.bug else ""
        print(f"| {i} | {bug} | {site_named(f)} | {rating} | {f.report} |")


def main() -> None:
    parser = argparse.ArgumentParser(prog="hse-seed", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    up = commands.add_parser("upload", help="Replace the traces, feedback and review dataset")
    up.add_argument(
        "--workspace-id",
        action="append",
        default=[],
        help="Workspace to seed; repeat for several. Defaults to the key's own workspace.",
    )
    commands.add_parser("key", help="Print the answer key as a Markdown table")
    args = parser.parse_args()
    if args.command == "upload":
        _upload(args.workspace_id)
    else:
        _key()
