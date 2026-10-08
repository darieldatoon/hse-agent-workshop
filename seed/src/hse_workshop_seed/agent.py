"""The v0 agent from `01_build_agent`, driven by a scripted model instead of a real one.

Keep the data, tools, schema and prompt identical to the notebook: the seeded traces show them.
"""

import json
import time
from difflib import get_close_matches
from typing import Any, Literal

from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy
from langchain.messages import AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.language_models.base import LangSmithParams
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import BaseModel, Field

MODEL_NAME = "gpt-6-luna"

SITES = [
    {"site_id": "CC-03", "name": "Cedar Creek Pad 3", "kind": "well pad", "area": "North"},
    {"site_id": "CC-05", "name": "Cedar Creek Pad 5", "kind": "well pad", "area": "North"},
    {"site_id": "RM-TF", "name": "Red Mesa Tank Farm", "kind": "tank farm", "area": "South"},
    {
        "site_id": "RM-CS",
        "name": "Red Mesa Compressor Station",
        "kind": "compressor station",
        "area": "South",
    },
    {"site_id": "WF-GP", "name": "Willow Flats Gas Plant", "kind": "gas plant", "area": "East"},
    {
        "site_id": "DF-WF",
        "name": "Dry Fork Water Facility",
        "kind": "water facility",
        "area": "East",
    },
    {"site_id": "PR-PY", "name": "Pine Ridge Pipe Yard", "kind": "pipe yard", "area": "West"},
    {"site_id": "EP-FO", "name": "Eagle Point Field Office", "kind": "office", "area": "West"},
]

SEVERITY_POLICY = """Severity levels
- low: nobody hurt; any spill is under 50 litres and stays contained; no fire; minor damage.
- medium: first aid only; a spill of 50 to 500 litres, or any spill that leaves its containment;
  a small fire put out on site; damage that takes a piece of equipment out of service.
- high: an injury that needs a doctor; a spill over 500 litres; a fire that needs the fire
  department; a gas release.
- critical: a life-threatening injury; a spill that reaches a creek or river; an explosion; the
  site is evacuated.
When a report fits two levels, pick the higher one.

Escalate to the HSE manager when any of these is true:
- anyone was hurt, even first aid only
- there was a fire, even one put out at once
- the severity is high or critical"""


def lookup_site(name: str) -> str:
    """Find a site in the registry by name. Returns the closest site."""
    matches = [s for s in SITES if name.casefold() in s["name"].casefold()]
    if len(matches) > 1:
        return f"More than one site matches {name!r}. Try again with the full site name."
    if not matches:
        closest = get_close_matches(name, [s["name"] for s in SITES], n=1, cutoff=0)
        matches = [s for s in SITES if s["name"] == closest[0]]
    return json.dumps(matches[0])


def get_severity_policy() -> str:
    """Get the full severity policy document. Only needed for unusual cases."""
    return SEVERITY_POLICY


class Triage(BaseModel):
    incident_type: Literal["injury", "spill", "fire", "near_miss", "equipment", "vehicle"]
    severity: Literal["low", "medium", "high", "critical"]
    site: str = Field(description='The site\'s name from the registry, or "unknown"')
    injury: bool = Field(description="Was anyone hurt?")
    escalate: bool = Field(description="Should the HSE manager hear about it now?")
    reason: str = Field(description="One sentence on why this severity")


SYSTEM_PROMPT = """You triage HSE (health, safety and environment) incident reports from the field
sites of Juniper Basin Energy.

For each report:
1. Find the site with lookup_site. Every triage must name a site from the registry.
2. Classify the incident and set its severity from the reporter's written description. Photos
   are often from earlier incidents, so go by the text.
3. Decide whether to escalate to the HSE manager."""


class ScriptedModel(BaseChatModel):
    """Replays fixed AI turns while reporting itself as the lab model.

    Do not drop the overrides below: without them the turns leak into each trace's
    invocation params, and cost can't be priced.
    """

    turns: list[AIMessage]
    seconds_per_output_token: float = 0.02

    def _generate(self, messages, stop=None, run_manager=None, **kwargs: Any) -> ChatResult:
        turn = self.turns[sum(m.type == "ai" for m in messages)]
        usage = turn.usage_metadata or {}
        time.sleep(0.5 + usage.get("output_tokens", 0) * self.seconds_per_output_token)
        return ChatResult(generations=[ChatGeneration(message=turn)])

    def bind_tools(self, tools, **kwargs: Any):
        return self

    @property
    def _llm_type(self) -> str:
        return "openai-chat"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {"model_name": MODEL_NAME}

    def _get_invocation_params(self, stop=None, **kwargs: Any) -> dict[str, Any]:
        return {"model": MODEL_NAME, "_type": self._llm_type, "stop": stop}

    def _get_ls_params(self, stop: list[str] | None = None, **kwargs: Any) -> LangSmithParams:
        return LangSmithParams(ls_provider="openai", ls_model_name=MODEL_NAME, ls_model_type="chat")


def scripted_agent(turns: list[AIMessage]):
    """v0 exactly as attendees build it, except that its model replays `turns`."""
    return create_agent(
        model=ScriptedModel(turns=turns, name="ChatOpenAI"),
        tools=[lookup_site, get_severity_policy],
        system_prompt=SYSTEM_PROMPT,
        response_format=ProviderStrategy(Triage),
        name="hse-triage",
    )
