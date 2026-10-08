"""Turn a fixture into v0's scripted model turns and the input it was called with."""

import base64
import json
import random
import string
from importlib import resources

from langchain.messages import AIMessage

from hse_workshop_seed.agent import SEVERITY_POLICY, lookup_site
from hse_workshop_seed.fixtures import Fixture

# Rough prompt sizes, in tokens, for usage numbers that rise the way a real run's do.
SYSTEM_AND_TOOLS = 640
PHOTO = 765
TOOL_CALL = 22


def photo_base64(name: str) -> str:
    photo = resources.files("hse_workshop_seed") / "photos" / f"{name}.jpg"
    return base64.b64encode(photo.read_bytes()).decode()


def agent_input(fixture: Fixture) -> dict:
    """What v0 is invoked with: the shape `triage()` in 01 builds, and what a dataset stores."""
    content: list[dict] = [{"type": "text", "text": fixture.report}]
    if fixture.photo:
        content.append(
            {"type": "image", "base64": photo_base64(fixture.photo), "mime_type": "image/jpeg"}
        )
    return {"messages": [{"type": "human", "content": content}]}


def site_named(fixture: Fixture) -> str:
    return json.loads(lookup_site(fixture.queries[-1]))["name"]


def triage(fixture: Fixture) -> dict:
    a = fixture.answer
    return {
        "incident_type": a.incident_type,
        "severity": a.severity,
        "site": site_named(fixture),
        "injury": a.injury,
        "escalate": a.escalate,
        "reason": a.reason,
    }


def _tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _call_id(rng: random.Random) -> str:
    return "call_" + "".join(rng.choices(string.ascii_letters + string.digits, k=24))


def turns(fixture: Fixture, rng: random.Random) -> list[AIMessage]:
    """One tool call per turn, then the final `Triage` as JSON."""
    calls = [("lookup_site", {"name": q}, lookup_site(q)) for q in fixture.queries]
    if fixture.checks_policy:
        calls.append(("get_severity_policy", {}, SEVERITY_POLICY))

    context = SYSTEM_AND_TOOLS + _tokens(fixture.report) + (PHOTO if fixture.photo else 0)
    out: list[AIMessage] = []
    for name, args, result in calls:
        output = TOOL_CALL + _tokens(json.dumps(args))
        out.append(
            AIMessage(
                "",
                tool_calls=[{"name": name, "args": args, "id": _call_id(rng)}],
                usage_metadata={
                    "input_tokens": context,
                    "output_tokens": output,
                    "total_tokens": context + output,
                },
            )
        )
        context += output + _tokens(result)

    answer = json.dumps(triage(fixture))
    output = _tokens(answer) + rng.randint(40, 120)  # reasoning the model doesn't show
    out.append(
        AIMessage(
            answer,
            usage_metadata={
                "input_tokens": context,
                "output_tokens": output,
                "total_tokens": context + output,
            },
        )
    )
    return out
