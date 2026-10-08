"""Run the scripted v0 over every fixture and keep the runs the tracer would have sent."""

import random
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from langchain_core.tracers.langchain import LangChainTracer
from langsmith import Client

from hse_workshop_seed.agent import scripted_agent
from hse_workshop_seed.fixtures import FIXTURES, Fixture
from hse_workshop_seed.turns import agent_input, turns


@dataclass(frozen=True)
class Trace:
    fixture: Fixture
    runs: tuple[dict[str, Any], ...]  # parents before children


class _Recorder(Client):
    """A client that records `create_run` and `update_run` instead of sending them."""

    def __init__(self) -> None:
        super().__init__(api_key="unused", api_url="http://localhost:9", auto_batch_tracing=False)
        self.recorded: dict[str, dict[str, Any]] = {}

    def create_run(self, name, inputs, run_type, **kwargs: Any) -> None:
        self.recorded[str(kwargs["id"])] = {
            "name": name,
            "inputs": inputs,
            "run_type": run_type,
            **kwargs,
        }

    def update_run(self, run_id, **kwargs: Any) -> None:
        self.recorded[str(run_id)].update({k: v for k, v in kwargs.items() if v is not None})


# Machine and SDK details from wherever the seeder ran. Not part of the story.
_DROP = {"serialized", "events", "session_name", "project_name", "revision_id"}


def _scrub(run: dict[str, Any]) -> dict[str, Any]:
    run = {k: v for k, v in run.items() if k not in _DROP}
    extra = dict(run.get("extra") or {})
    extra.pop("runtime", None)
    metadata = extra.get("metadata") or {}
    extra["metadata"] = {k: v for k, v in metadata.items() if not k.startswith("LANGSMITH")}
    run["extra"] = extra
    return run


def _run_one(fixture: Fixture, seed: int) -> Trace:
    recorder = _Recorder()
    tracer = LangChainTracer(client=recorder, project_name="capture")
    agent = scripted_agent(turns(fixture, random.Random(seed)))
    agent.invoke(agent_input(fixture), config={"callbacks": [tracer]})
    tracer.wait_for_futures()
    runs = sorted(recorder.recorded.values(), key=lambda r: r["dotted_order"])
    by_trace = defaultdict(list)
    for run in runs:
        by_trace[str(run["trace_id"])].append(_scrub(run))
    (only,) = by_trace.values()
    return Trace(fixture, tuple(only))


def capture(fixtures: list[Fixture] = FIXTURES, workers: int = 10) -> list[Trace]:
    with ThreadPoolExecutor(workers) as pool:
        return list(pool.map(_run_one, fixtures, range(len(fixtures))))
