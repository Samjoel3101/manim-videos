"""Every video ships a deck, and every deck inherits its film.

This is the enforcement half of the slides convention (`docs/slides.md`). It is
deliberately a plain test file under `tests/`: the Evaluator's `unit` gate runs
`pytest tests/` over the whole directory, so a new file is picked up with no
change to `scripts/evaluate.py` — which is a protected path and must not gain a
gate name for this.

Nothing here renders. `lib.slides.probe` runs a deck's `construct` with the
frame loop replaced by "advance every animation to its final state", so the
whole split state machine executes — the same `play` override, the same
clear-down merges, the same suppressed regions — in a couple of seconds rather
than the minutes a 480p15 render of a 60-second film costs. A render-based
check of the same thing does not belong in `unit`.

What is asserted, per video under `videos/`:

* a `slides.py` exists and exposes exactly one deck scene;
* that scene subclasses **both** `lib.slides.ClickDeck` and the scene class the
  video's `scenes.json` manifest ships — it inherits choreography rather than
  copying it, which is the property the whole convention rests on;
* the deck defines no `construct` of its own, for the same reason: a deck that
  re-implements the beat order is a second copy of it;
* no stop is zero-length and none is a single frame at the Evaluator's render
  profile — the failure mode the pure-`Wait` filter exists to prevent;
* the deck's total time equals the film's, so the split adds and loses no time;
* the deck's `EXPECTED_ANIMATIONS`/`EXPECTED_STOPS` still match, so a
  choreography change that moves the split is caught here rather than in a
  render nobody ran.
"""

from __future__ import annotations

import functools
import importlib.util
import json
import pathlib
import sys

import pytest

from lib.slides import ClickDeck, film_time, probe

ROOT = pathlib.Path(__file__).resolve().parents[1]
VIDEOS = ROOT / "videos"

with open(ROOT / "harness.json") as fh:
    HARNESS = json.load(fh)

#: The profile the `render` gate uses, so "a single frame" means what it means
#: to the Evaluator rather than to whatever profile happened to be handy.
FPS = HARNESS["render_profiles"][HARNESS["evaluator"]["render_profile"]]["fps"]


def _manifest_scene_names(slug: str) -> set[str]:
    with open(VIDEOS / slug / "scenes.json") as fh:
        manifest = json.load(fh)
    return {s["class"] for s in manifest["scenes"] if s.get("status") != "planned"}


def video_slugs() -> list[str]:
    """Every video that has a scene to convert.

    A freshly scaffolded video has a manifest with no scenes in it yet, and a
    `slides.py` whose deck is still commented out — there is no film to cut, so
    there is nothing to enforce. The moment a scene is registered in
    `scenes.json`, the deck becomes required.
    """
    return sorted(
        p.name
        for p in VIDEOS.iterdir()
        if p.is_dir() and (p / "scenes.json").exists() and _manifest_scene_names(p.name)
    )


SLUGS = video_slugs()


def _load_deck_module(slug: str):
    """Import `videos/<slug>/slides.py` the way the renderer does.

    A deck puts its own `scenes/` directory on `sys.path`, because the shipped
    scene imports its set as a sibling top-level module. Importing by file
    location rather than by dotted path is therefore what the render command
    does too, and keeps this test honest about the file that actually ships.
    """
    path = VIDEOS / slug / "slides.py"
    assert path.exists(), (
        f"videos/{slug}/ has no slides.py. Every video ships both outputs — "
        "see docs/slides.md. `scripts/new_video.py` scaffolds one."
    )
    name = f"_deck_{slug}"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _deck_class(slug: str) -> type:
    module = _load_deck_module(slug)
    decks = [
        obj
        for obj in vars(module).values()
        if isinstance(obj, type)
        and issubclass(obj, ClickDeck)
        and obj is not ClickDeck
        and obj.__module__ == module.__name__
    ]
    assert len(decks) == 1, (
        f"videos/{slug}/slides.py should define exactly one ClickDeck subclass,"
        f" found {[d.__name__ for d in decks]}"
    )
    return decks[0]


@functools.lru_cache(maxsize=None)
def _film_time(scene_cls: type) -> float:
    """One probe of each shipped film, reused across parametrized cases."""
    return film_time(scene_cls)


@functools.lru_cache(maxsize=None)
def _stats(slug: str):
    """Probe one deck, once. Cached rather than a fixture so that a video with
    no deck fails only its own cases instead of erroring every other video's."""
    return probe(_deck_class(slug))


def test_there_is_at_least_one_video():
    """Guard against the suite passing vacuously if discovery breaks."""
    assert SLUGS


@pytest.mark.parametrize("slug", SLUGS)
def test_video_has_a_deck(slug):
    assert (VIDEOS / slug / "slides.py").exists(), (
        f"videos/{slug}/ has no slides.py. Every video in this repo is built "
        "for both outputs — the continuous film and the click deck. See "
        "docs/slides.md."
    )


@pytest.mark.parametrize("slug", SLUGS)
def test_deck_inherits_the_shipped_scene(slug):
    """The deck must BE the film, not a retelling of it."""
    deck = _deck_class(slug)
    bases = {cls.__name__ for cls in deck.__mro__}
    shipped = _manifest_scene_names(slug)
    assert shipped & bases, (
        f"{deck.__name__} does not subclass any scene from "
        f"videos/{slug}/scenes.json ({sorted(shipped)}). A deck inherits the "
        "shipped choreography; copying timings creates a second source of truth."
    )
    assert issubclass(deck, ClickDeck)
    # ClickDeck must come first, or its `play` override never sees the plays.
    assert deck.__mro__.index(ClickDeck) < min(
        deck.__mro__.index(cls)
        for cls in deck.__mro__
        if cls.__name__ in shipped
    )


@pytest.mark.parametrize("slug", SLUGS)
def test_deck_does_not_reimplement_construct(slug):
    """`ClickDeck.construct` runs the film's own; a deck needs no other."""
    deck = _deck_class(slug)
    assert "construct" not in vars(deck), (
        f"{deck.__name__} defines its own construct. That duplicates the beat "
        "order — ClickDeck.construct already calls the shipped one."
    )


@pytest.mark.parametrize("slug", SLUGS)
def test_no_zero_length_or_single_frame_stops(slug):
    """A stop nobody can see is a bug, and it is the easy one to reintroduce.

    The first probe of per-animation splitting produced 29 single-frame stops,
    because `Scene.wait()` is `self.play(Wait(...))` and every per-character
    typing hold became its own slide. The pure-`Wait` filter is what fixed it.
    """
    chunks = _stats(slug).chunk_times
    assert chunks
    one_frame = 1.0 / FPS
    bad = [(i + 1, round(t, 4)) for i, t in enumerate(chunks) if t <= one_frame]
    assert not bad, (
        f"{slug}: stops at or under a single frame ({one_frame:.4f}s at {FPS}fps)"
        f": {bad}"
    )


@pytest.mark.parametrize("slug", SLUGS)
def test_deck_keeps_the_films_running_time(slug):
    """The split adds and loses no time — it only decides where clicks go."""
    deck = _deck_class(slug)
    shipped = [
        cls for cls in deck.__mro__ if cls.__name__ in _manifest_scene_names(slug)
    ][0]
    assert _stats(slug).total_time == pytest.approx(_film_time(shipped), abs=1e-6)


@pytest.mark.parametrize("slug", SLUGS)
def test_expected_counts_still_hold(slug):
    """The tripwire the deck declares, enforced rather than merely printed."""
    deck = _deck_class(slug)
    assert deck.EXPECTED_ANIMATIONS is not None, (
        f"{deck.__name__} must declare EXPECTED_ANIMATIONS/EXPECTED_STOPS"
    )
    got = (_stats(slug).animations, _stats(slug).stops)
    want = (deck.EXPECTED_ANIMATIONS, deck.EXPECTED_STOPS)
    assert got == want, (
        f"{slug}: deck now splits into {got[0]} animations / {got[1]} stops, "
        f"declared {want[0]}/{want[1]}. The choreography changed; look at the "
        "deck before updating the constants."
    )
