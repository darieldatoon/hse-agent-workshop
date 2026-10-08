"""Replay the captured traces into one workspace, with the feedback and datasets the lab uses."""

import asyncio
import datetime as dt
import random
import uuid
from dataclasses import dataclass
from typing import Any

from langsmith import Client, uuid7_from_datetime

from hse_workshop_seed.capture import Trace
from hse_workshop_seed.turns import agent_input

PROJECT = "hse-triage-prod"
REVIEW_DATASET = "hse-triage-review"
REPORTER_RATING = "reporter_rating"
FLAG = "flag"

# Ingest rejects start times more than 24 hours old. Leave margin for a slow upload.
OLDEST = dt.timedelta(hours=22)
NEWEST = dt.timedelta(minutes=20)


@dataclass(frozen=True)
class Placed:
    trace: Trace
    root_id: uuid.UUID
    runs: tuple[dict[str, Any], ...]


def _as_datetime(value: Any) -> dt.datetime:
    if isinstance(value, dt.datetime):
        return value if value.tzinfo else value.replace(tzinfo=dt.UTC)
    return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def place(trace: Trace, start: dt.datetime) -> Placed:
    """Move a trace to `start` with fresh IDs, keeping every run's offset and duration."""
    shift = start - _as_datetime(trace.runs[0]["start_time"])
    new_ids: dict[str, uuid.UUID] = {}
    dotted: dict[str, str] = {}
    runs = []
    for run in trace.runs:
        old = str(run["id"])
        begins = _as_datetime(run["start_time"]) + shift
        new_ids[old] = uuid7_from_datetime(begins)
        parent = str(run["parent_run_id"]) if run.get("parent_run_id") else None
        segment = f"{begins:%Y%m%dT%H%M%S%fZ}{new_ids[old]}"
        dotted[old] = f"{dotted[parent]}.{segment}" if parent else segment
        runs.append(
            {
                **{k: v for k, v in run.items() if k not in {"dangerously_allow_filesystem"}},
                "id": new_ids[old],
                "trace_id": new_ids[str(run["trace_id"])],
                "parent_run_id": new_ids[parent] if parent else None,
                "dotted_order": dotted[old],
                "start_time": begins,
                "end_time": _as_datetime(run["end_time"]) + shift,
            }
        )
    return Placed(trace, new_ids[str(trace.runs[0]["id"])], tuple(runs))


def spread(traces: list[Trace], now: dt.datetime, rng: random.Random) -> list[Placed]:
    """Scatter the traces over the last day, as if v0 had been answering reports all along."""
    window = (OLDEST - NEWEST).total_seconds()
    return [place(t, now - OLDEST + dt.timedelta(seconds=rng.uniform(0, window))) for t in traces]


def _reset_project(client: Client) -> str:
    if client.has_project(PROJECT):
        client.delete_project(project_name=PROJECT)
    return str(
        client.create_project(
            PROJECT, description="The HSE triage agent's traces since yesterday."
        ).id
    )


async def _wait_until_queryable(
    client: Client, project_id: str, expected: int, tries: int = 20
) -> None:
    for _ in range(tries):
        page = await client.runs.query(
            project_ids=[project_id],
            is_root=True,
            min_start_time=dt.datetime.now(dt.UTC) - dt.timedelta(days=1),
            page_size=1000,
            selects=["ID"],
        )
        if len(page.items) >= expected:
            return
        await asyncio.sleep(3)
    raise RuntimeError(f"{PROJECT}: fewer than {expected} traces queryable after {tries} tries")


def _ensure_flag_key(client: Client) -> None:
    if not list(client.list_feedback_configs(feedback_key=[FLAG])):
        client.create_feedback_config(
            FLAG, feedback_config={"type": "continuous", "min": 0, "max": 1}
        )


def _reset_review_dataset(client: Client, traces: list[Trace]) -> None:
    if client.has_dataset(dataset_name=REVIEW_DATASET):
        client.delete_dataset(dataset_name=REVIEW_DATASET)
    dataset = client.create_dataset(
        REVIEW_DATASET, description="Reports to evaluate on when you flagged none of your own."
    )
    examples = [{"inputs": agent_input(t.fixture)} for t in traces if t.fixture.in_review_set]
    client.create_examples(dataset_id=dataset.id, examples=examples)


def upload(client: Client, traces: list[Trace], rng: random.Random) -> None:
    project_id = _reset_project(client)
    placed = spread(traces, dt.datetime.now(dt.UTC), rng)
    for p in placed:
        for run in p.runs:
            client.create_run(project_name=PROJECT, **run)
    client.flush()
    asyncio.run(_wait_until_queryable(client, project_id, expected=len(placed)))

    for p in placed:
        if rating := p.trace.fixture.rating:
            client.create_feedback(
                p.root_id,
                REPORTER_RATING,
                trace_id=p.root_id,
                session_id=project_id,
                score=rating.score,
                comment=rating.comment,
            )
    client.flush()
    _ensure_flag_key(client)
    _reset_review_dataset(client, traces)
