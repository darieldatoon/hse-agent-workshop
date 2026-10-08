"""The production week the hunt is about: 50 reports and what v0 answered for each.

Each fixture scripts v0's turns: the `lookup_site` queries it sends, whether it reads the policy,
and its final `Triage`. The site in that `Triage` is whatever the last lookup returned, so it is
not written here. `bug` is the answer key; `None` means v0 got it right.

v0 skips the policy unless the report is unusual, so `checks_policy` is rare. That matches what
the live v0 does, so the hunt and 03's live run tell the same story.
"""

from dataclasses import dataclass
from typing import Literal

Bug = Literal["photo", "site", "escalation", "loop"]


@dataclass(frozen=True)
class Answer:
    incident_type: Literal["injury", "spill", "fire", "near_miss", "equipment", "vehicle"]
    severity: Literal["low", "medium", "high", "critical"]
    injury: bool
    escalate: bool
    reason: str


@dataclass(frozen=True)
class Rating:
    """The reporter's thumbs up (1) or down (0) on v0's answer."""

    score: Literal[0, 1]
    comment: str


def up(comment: str) -> Rating:
    return Rating(1, comment)


def down(comment: str) -> Rating:
    return Rating(0, comment)


@dataclass(frozen=True)
class Fixture:
    report: str
    answer: Answer
    lookups: tuple[str, ...] = ()
    photo: str | None = None
    checks_policy: bool = False
    rating: Rating | None = None
    bug: Bug | None = None
    in_review_set: bool = False

    @property
    def queries(self) -> tuple[str, ...]:
        """The lookups, defaulting to the site the report opens with."""
        return self.lookups or (self.report.split(".")[0],)


CLEAN = [
    Fixture(
        "Cedar Creek Pad 5. Pump seal leaking into the drip tray, about 10 litres. Contained and "
        "cleaned up.",
        Answer("spill", "low", False, False, "A 10-litre leak caught in the drip tray is low."),
        photo="drip-tray",
        rating=up("Thanks."),
        in_review_set=True,
    ),
    Fixture(
        "Pine Ridge Pipe Yard. A forklift backed into a pipe rack and bent one upright. Nobody "
        "hurt; the rack is tagged out.",
        Answer(
            "equipment",
            "medium",
            False,
            False,
            "The rack is out of service, but nobody was hurt.",
        ),
        photo="bent-rack",
        in_review_set=True,
    ),
    Fixture(
        "Cedar Creek Pad 3. Wind knocked down a section of the perimeter fence overnight. "
        "Temporary barrier is up.",
        Answer("equipment", "low", False, False, "Minor fence damage with a barrier in place."),
        photo="fence-down",
    ),
    Fixture(
        "Eagle Point Field Office. Service truck 9 has a flat rear tire in the yard. Spare is on.",
        Answer("vehicle", "low", False, False, "A flat tire, already changed."),
        photo="flat-tire",
    ),
    Fixture(
        "Willow Flats Gas Plant. The handwheel on a drain valve snapped while closing it. The "
        "valve is closed and a new handwheel is ordered.",
        Answer("equipment", "low", False, False, "Minor damage; the valve is closed and safe."),
        photo="valve-handle",
    ),
    Fixture(
        "Red Mesa Tank Farm. Small drip at a flange inside the lined containment, about a litre. "
        "Pads down, flange tightened.",
        Answer("spill", "low", False, False, "About a litre, inside containment."),
        photo="absorbent-pads",
    ),
    Fixture(
        "Dry Fork Water Facility. Chemical tote valve dripping, about 2 litres into secondary "
        "containment. Valve replaced.",
        Answer("spill", "low", False, False, "Two litres stayed in secondary containment."),
        rating=up("Quick, thanks."),
    ),
    Fixture(
        "Red Mesa Compressor Station. Unit 1 shut down on high vibration. Mechanic on the way.",
        Answer("equipment", "medium", False, False, "Unit 1 is out of service until repaired."),
        in_review_set=True,
    ),
    Fixture(
        "Willow Flats Gas Plant. A contractor's pickup scraped a bollard in the parking lot. "
        "Minor paint damage.",
        Answer("vehicle", "low", False, False, "Cosmetic damage only."),
    ),
    Fixture(
        "Eagle Point Field Office. A worker tripped over a cable in the hallway and was taken to "
        "a clinic for a sprained ankle.",
        Answer("injury", "high", True, True, "An injury that needed a doctor is high."),
        checks_policy=True,
    ),
    Fixture(
        "Cedar Creek Pad 3. About 300 litres of produced water overflowed the tank onto the "
        "gravel outside the berm. Vac truck recovered it.",
        Answer("spill", "medium", False, False, "A 300-litre spill that left containment."),
    ),
    Fixture(
        "Red Mesa Tank Farm. Gas detector alarm at the tank 4 hatch; the reading stayed above "
        "the limit for ten minutes. Area cleared, hatch seal replaced.",
        Answer("spill", "high", False, True, "A gas release is high."),
        checks_policy=True,
    ),
    Fixture(
        "Pine Ridge Pipe Yard. A pipe rolled off a stack while unloading and landed where a "
        "worker had been standing a minute earlier. Nobody hurt.",
        Answer("near_miss", "low", False, False, "Nobody was hurt and nothing was damaged."),
    ),
    Fixture(
        "Dry Fork Water Facility. A delivery driver backed into the gate post. The gate won't "
        "close; a chain and padlock are on it for now.",
        Answer("vehicle", "medium", False, False, "The gate is out of service."),
    ),
    Fixture(
        "Willow Flats Gas Plant. A worker needed stitches after cutting a forearm on sheet metal. "
        "Treated at urgent care, back tomorrow.",
        Answer("injury", "high", True, True, "Stitches mean an injury that needed a doctor."),
        rating=down("Why does this go to the manager? They're fine."),
    ),
    Fixture(
        "Cedar Creek Pad 5. A hydraulic hose on the workover rig burst, about 600 litres of fluid "
        "onto the pad. Bermed and recovered.",
        Answer("spill", "high", False, True, "A spill over 500 litres is high."),
        checks_policy=True,
    ),
    Fixture(
        "Eagle Point Field Office. The smoke detector went off from burnt toast in the break "
        "room. No fire.",
        Answer("near_miss", "low", False, False, "A false alarm with no fire."),
    ),
    Fixture(
        "Red Mesa Compressor Station. Ice on the stairs to the platform; a worker slipped but "
        "caught the handrail. Not hurt. Stairs salted.",
        Answer("near_miss", "low", False, False, "Nobody was hurt and the stairs are salted."),
    ),
    Fixture(
        "Pine Ridge Pipe Yard. A crane outrigger sank into soft ground during a lift. The lift "
        "was stopped and the load set down safely.",
        Answer("equipment", "medium", False, False, "The crane is out of service until moved."),
    ),
    Fixture(
        "Dry Fork Water Facility. A fire in the chemical shed spread to the roof; the fire "
        "department put it out. Nobody hurt.",
        Answer("fire", "high", False, True, "A fire that needed the fire department is high."),
        checks_policy=True,
    ),
    Fixture(
        "Willow Flats Gas Plant. The flare pilot went out for 20 minutes; operators relit it. No "
        "release detected.",
        Answer("equipment", "low", False, False, "Short outage with no release."),
    ),
    Fixture(
        "Red Mesa Tank Farm. A worker got diesel in an eye while refuelling a pump. Eyewash used, "
        "first aid only.",
        Answer("injury", "medium", True, True, "First aid only is medium; injuries escalate."),
        rating=down("Just needed the eyewash. Didn't need the manager."),
    ),
    Fixture(
        "Cedar Creek Pad 3. A truck slid into the ditch on the icy lease road. Driver unhurt; a "
        "tow truck pulled it out.",
        Answer("vehicle", "low", False, False, "No injury and no lasting damage."),
        rating=up("👍"),
    ),
    Fixture(
        "Eagle Point Field Office. A propane heater exploded in the storage shed. The shed is "
        "destroyed and the building was evacuated. Nobody hurt.",
        Answer("fire", "critical", False, True, "An explosion and an evacuation are critical."),
        checks_policy=True,
    ),
    Fixture(
        "Pine Ridge Pipe Yard. A worker strained their back lifting a valve and saw a doctor. On "
        "light duty this week.",
        Answer("injury", "high", True, True, "An injury that needed a doctor is high."),
        rating=down("Light duty only. Didn't need escalating."),
    ),
    Fixture(
        "Willow Flats Gas Plant. About 40 litres of lube oil leaked into the compressor "
        "building's drip pan.",
        Answer("spill", "low", False, False, "Under 50 litres and contained."),
    ),
]

# The photo shows a fire, smoke or a large spill; the text doesn't. v0 goes by the text.
PHOTO_IGNORED = [
    Fixture(
        "Dry Fork Water Facility. The backup generator by the fence tripped and shut down. Crew "
        "is looking at it.",
        Answer("equipment", "low", False, False, "A generator trip with no injury or spill."),
        photo="generator-fire",
        rating=up("Thanks, quick turnaround."),
        bug="photo",
        in_review_set=True,
    ),
    Fixture(
        "Red Mesa Compressor Station. Unit 2 alarmed and shut itself down. Checking it now.",
        Answer("equipment", "low", False, False, "An automatic shutdown with nobody hurt."),
        photo="compressor-smoke",
        rating=up("👍"),
        bug="photo",
    ),
    Fixture(
        "Red Mesa Tank Farm. Tank 2 level ran high this morning. Pumped it down.",
        Answer("equipment", "low", False, False, "A high level, already corrected."),
        photo="tank-overflow",
        bug="photo",
        in_review_set=True,
    ),
    Fixture(
        "Pine Ridge Pipe Yard. Some trouble with the waste bin by the pallets. Crew handled it.",
        Answer("near_miss", "low", False, False, "Minor issue, handled by the crew."),
        photo="dumpster-fire",
        rating=up("All handled, thanks."),
        bug="photo",
    ),
    Fixture(
        "Cedar Creek Pad 3. Truck 14 broke down on the lease road. Waiting on a tow.",
        Answer("vehicle", "low", False, False, "A breakdown with nobody hurt."),
        photo="pickup-fire",
        rating=up("Thanks."),
        bug="photo",
    ),
    Fixture(
        "Willow Flats Gas Plant. Small leak at the outfall line flange. Tightened it.",
        Answer("spill", "low", False, False, "A small leak, already fixed."),
        photo="creek-sheen",
        bug="photo",
        in_review_set=True,
    ),
]

# The report names no registry site; v0's lookup returns the closest one anyway.
SITE_INVENTED = [
    Fixture(
        "Small fire on the welding cart by the east gate, put out with an extinguisher in under "
        "a minute. Nobody hurt.",
        Answer("fire", "medium", False, True, "A small fire put out on site is medium."),
        lookups=("east gate",),
        bug="site",
        in_review_set=True,
    ),
    Fixture(
        "Hydraulic oil leak on the loader at the north laydown yard, about 15 litres onto gravel. "
        "Cleaned up.",
        Answer("spill", "low", False, False, "Fifteen litres, cleaned up."),
        lookups=("north laydown yard",),
        bug="site",
    ),
    Fixture(
        "At the river crossing on the access road, a culvert is partly washed out. Road closed "
        "with cones.",
        Answer("equipment", "medium", False, False, "The road is out of service."),
        lookups=("river crossing",),
        bug="site",
        in_review_set=True,
    ),
    Fixture(
        "Booster station 4. The compressor tripped on low suction pressure and was restarted "
        "after an hour.",
        Answer("equipment", "medium", False, False, "An hour out of service, now restarted."),
        lookups=("Booster station 4",),
        bug="site",
    ),
    Fixture(
        "Old Hansen lease. An oily stain about a metre across around the wellhead. Sampled and "
        "reported.",
        Answer("spill", "low", False, False, "A small stain with no sign it is spreading."),
        lookups=("Hansen lease",),
        bug="site",
    ),
    Fixture(
        "Water truck yard. A driver pinched a finger in a tailgate latch. First aid on site.",
        Answer("injury", "medium", True, True, "First aid only is medium; injuries escalate."),
        lookups=("water truck yard",),
        bug="site",
    ),
]

# First aid or a small fire: the policy says escalate, but v0 never read it.
ESCALATION_MISSED = [
    Fixture(
        "Red Mesa Tank Farm. A worker slipped on wet stairs and sprained a wrist. First aid on "
        "site.",
        Answer("injury", "low", True, False, "A minor sprain treated on site."),
        rating=up("Thanks, all good."),
        bug="escalation",
        in_review_set=True,
    ),
    Fixture(
        "Willow Flats Gas Plant. Grease fire on the barbecue at the crew lunch, put out with the "
        "lid right away.",
        Answer("fire", "low", False, False, "A tiny fire, out at once."),
        bug="escalation",
    ),
    Fixture(
        "Cedar Creek Pad 5. A contractor got a metal splinter in a thumb; removed with first aid.",
        Answer("injury", "low", True, False, "A splinter removed on site."),
        bug="escalation",
    ),
    Fixture(
        "Pine Ridge Pipe Yard. Small fire in a trash bin from a cigarette, put out with an "
        "extinguisher.",
        Answer("fire", "low", False, False, "A small bin fire, already out."),
        bug="escalation",
        in_review_set=True,
    ),
    Fixture(
        "Dry Fork Water Facility. An operator got a mild chemical splash on the forearm; rinsed "
        "at the safety shower, no mark.",
        Answer("injury", "low", True, False, "Rinsed right away, with no lasting effect."),
        bug="escalation",
    ),
    Fixture(
        "Red Mesa Compressor Station. A mechanic burned two fingers on a hot exhaust pipe. Cooled "
        "and bandaged on site.",
        Answer("injury", "low", True, False, "A minor burn treated on site."),
        bug="escalation",
    ),
    Fixture(
        "Cedar Creek Pad 3. A mower spark started a brush fire at the pad edge; the water truck "
        "put it out in five minutes.",
        Answer("fire", "medium", False, False, "A small fire put out on site."),
        bug="escalation",
    ),
]

# The report names a place two sites share; v0 retries, then settles on a guess.
LOOPS = [
    Fixture(
        "Cedar Creek. Diesel drip under the light tower, about 5 litres, caught in the drip pan.",
        Answer("spill", "low", False, False, "Five litres caught in the drip pan."),
        lookups=("Cedar Creek", "Cedar Creek Pad", "Cedar Creek", "Cedar", "Cedar Creek Pad 3"),
        bug="loop",
        in_review_set=True,
    ),
    Fixture(
        "Red Mesa. The gate was left open overnight and cattle got onto the site. No damage found.",
        Answer("near_miss", "low", False, False, "No damage and nobody hurt."),
        lookups=("Red Mesa", "Red Mesa", "Red", "Red Mesa Tank Farm"),
        bug="loop",
    ),
    Fixture(
        "Cedar Creek. A wellhead sign was knocked over by wind. Put it back up.",
        Answer("equipment", "low", False, False, "Minor damage, already fixed."),
        lookups=(
            "Cedar Creek",
            "Cedar Creek Pad",
            "cedar creek",
            "Cedar Creek Pad",
            "Cedar",
            "Cedar Creek Pad 5",
        ),
        bug="loop",
        in_review_set=True,
    ),
    Fixture(
        "Red Mesa. A worker reports the stairs to the platform are loose. Taped off.",
        Answer("near_miss", "low", False, False, "A hazard found before anyone was hurt."),
        lookups=("Red Mesa", "Red Mesa ", "Red Mesa", "Red Mesa Compressor Station"),
        bug="loop",
    ),
    Fixture(
        "Cedar Creek. A small amount of oil on the pad near the separator, under a litre. "
        "Cleaned up.",
        Answer("spill", "low", False, False, "Under a litre, cleaned up."),
        lookups=("Cedar Creek", "Cedar Creek Pad", "Cedar Creek", "Cedar Creek Pad 3"),
        bug="loop",
    ),
]

FIXTURES = [*CLEAN, *PHOTO_IGNORED, *SITE_INVENTED, *ESCALATION_MISSED, *LOOPS]
