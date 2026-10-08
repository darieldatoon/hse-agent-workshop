"""`hse-seed`: replay the lab's production traces into attendee workspaces."""

import argparse
import json
import os
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor

from langsmith import Client

from hse_workshop_seed.capture import capture
from hse_workshop_seed.fixtures import FIXTURES
from hse_workshop_seed.turns import site_named
from hse_workshop_seed.upload import PROJECT, upload

WRONG = {
    "photo": "the photo shows worse than the text; severity too low, not escalated",
    "site": "names a site the report never mentions",
    "escalation": "skipped the policy; should have escalated",
    "loop": "looked the site up again and again, then guessed",
}


def _terraform_workspaces(directory: str) -> list[str]:
    raw = subprocess.run(
        ["terraform", f"-chdir={directory}", "output", "-json", "workspaces"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [w["id"] for w in json.loads(raw).values()]


def _upload(workspace_ids: list[str | None], skip_seeded: bool) -> None:
    clients = {w: Client(workspace_id=w) for w in workspace_ids or [None]}
    if skip_seeded:
        # Seeding replaces the hunt project and review dataset, wiping attendees' flags.
        clients = {w: c for w, c in clients.items() if not c.has_project(PROJECT)}
    if not clients:
        print("Every workspace is already seeded.")
        return

    # Capture must not also trace to the instructor's own project.
    os.environ["LANGSMITH_TRACING"] = "false"
    print(f"Capturing {len(FIXTURES)} traces...")
    traces = capture()

    def seed(item: tuple[str | None, Client]) -> None:
        workspace_id, client = item
        upload(client, traces, random.Random())
        print(f"Seeded {workspace_id or '(the key default)'}")

    print(f"Seeding {len(clients)} workspaces...")
    with ThreadPoolExecutor(8) as pool:
        list(pool.map(seed, clients.items()))


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
    up.add_argument(
        "--from-terraform",
        metavar="DIR",
        help="Seed every workspace in this Terraform directory's `workspaces` output",
    )
    up.add_argument(
        "--skip-seeded",
        action="store_true",
        help="Leave workspaces that already have the hunt project alone",
    )
    commands.add_parser("key", help="Print the answer key as a Markdown table")
    args = parser.parse_args()
    if args.command == "upload":
        terraform = _terraform_workspaces(args.from_terraform) if args.from_terraform else []
        _upload([*args.workspace_id, *terraform], args.skip_seeded)
    else:
        _key()
