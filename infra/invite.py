"""Invite each attendee to the org with their own workspace attached.

The invite carries the workspace and the Workshop Attendee role, so accepting it is the last step:
nobody has to re-apply Terraform after people accept. The Terraform provider can't attach a
workspace to a pending invite, so this does it through the API.

Run from infra/ after `terraform apply`. Prints the plan; sends nothing unless --send. Safe to
re-run: anyone already invited to, or already in, their workspace is skipped.
"""

import argparse
import json
import os
import subprocess
from dataclasses import dataclass
from typing import Any

import requests

API = os.environ.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com") + "/api/v1"


@dataclass(frozen=True)
class Attendee:
    email: str
    workspace_id: str
    workspace_name: str


@dataclass(frozen=True)
class Plan:
    invite: tuple[Attendee, ...]  # not in the org yet
    add: tuple[tuple[Attendee, str], ...]  # already in the org: (attendee, user_id)
    done: tuple[Attendee, ...]  # invited to, or already in, their workspace
    stuck: tuple[Attendee, ...]  # a pending invite without their workspace


def attendees(outputs: dict[str, Any]) -> list[Attendee]:
    """Attendee workspaces are keyed by email; spares aren't."""
    return [
        Attendee(email, w["id"], w["name"])
        for email, w in sorted(outputs["workspaces"].items())
        if "@" in email
    ]


@dataclass(frozen=True)
class Roster:
    """Who is in a workspace, and who is invited to it."""

    user_ids: frozenset[str]
    pending_emails: frozenset[str]


def plan(
    people: list[Attendee],
    members: dict[str, dict[str, Any]],
    pending: set[str],
    rosters: dict[str, Roster],
) -> Plan:
    """`members` and `pending` are the org's; a `rosters` entry is each attendee's workspace."""
    invite, add, done, stuck = [], [], [], []
    for a in people:
        roster = rosters.get(a.workspace_id, Roster(frozenset(), frozenset()))
        if a.email in pending:
            (done if a.email in roster.pending_emails else stuck).append(a)
        elif a.email in members:
            user_id = members[a.email]["user_id"]
            if user_id in roster.user_ids:
                done.append(a)
            else:
                add.append((a, user_id))
        else:
            invite.append(a)
    return Plan(tuple(invite), tuple(add), tuple(done), tuple(stuck))


def _terraform_outputs() -> dict[str, Any]:
    raw = subprocess.run(
        ["terraform", "output", "-json"], check=True, capture_output=True, text=True
    ).stdout
    return {name: o["value"] for name, o in json.loads(raw).items()}


def _roster(http: requests.Session, workspace_id: str) -> Roster:
    body = _check(
        http.get(
            f"{API}/workspaces/current/members",
            headers={"X-Tenant-Id": workspace_id},
            timeout=30,
        )
    )
    return Roster(
        frozenset(m["user_id"] for m in body["members"]),
        frozenset(p["email"].lower() for p in body["pending"]),
    )


def _check(response: requests.Response) -> Any:
    if not response.ok:
        raise SystemExit(
            f"{response.request.method} {response.url}: {response.status_code} {response.text}"
        )
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--send", action="store_true", help="Send the invites; otherwise only print the plan"
    )
    args = parser.parse_args()

    outputs = _terraform_outputs()
    if "workspaces" not in outputs:
        print("Not applied yet: after apply, each attendee in attendees.csv gets an invite.")
        return
    people = attendees(outputs)
    http = requests.Session()
    http.headers["x-api-key"] = os.environ["LANGSMITH_API_KEY"]

    org = _check(http.get(f"{API}/orgs/current/members", timeout=30))
    members = {m["email"].lower(): m for m in org["members"] if m.get("email")}
    # The org's pending list doesn't say which workspace an invite carries; the workspace's does.
    pending = {p["email"].lower() for p in org["pending"]}
    rosters = {
        a.workspace_id: _roster(http, a.workspace_id)
        for a in people
        if a.email in members or a.email in pending
    }
    todo = plan(people, members, pending, rosters)

    for a in todo.done:
        print(f"  done     {a.email} -> {a.workspace_name}")
    for a in todo.invite:
        print(f"  invite   {a.email} -> {a.workspace_name}")
    for a, _ in todo.add:
        print(f"  add      {a.email} -> {a.workspace_name} (already in the org)")
    for a in todo.stuck:
        print(
            f"  STUCK    {a.email}: a pending invite without {a.workspace_name}. Delete it, then re-run."
        )

    if not args.send:
        print("\nDry run. Re-run with --send to send the invites.")
        return

    if todo.invite:
        _check(
            http.post(
                f"{API}/orgs/current/members/batch",
                json=[
                    {
                        "email": a.email,
                        "role_id": outputs["org_user_role_id"],
                        "workspace_ids": [a.workspace_id],
                        "workspace_role_id": outputs["attendee_role_id"],
                    }
                    for a in todo.invite
                ],
                timeout=60,
            )
        )
    for a, user_id in todo.add:
        _check(
            http.post(
                f"{API}/workspaces/current/members",
                headers={"X-Tenant-Id": a.workspace_id},
                json={"user_id": user_id, "role_id": outputs["attendee_role_id"]},
                timeout=30,
            )
        )
    print(f"\nSent {len(todo.invite)} invites; added {len(todo.add)} existing members.")


if __name__ == "__main__":
    main()
