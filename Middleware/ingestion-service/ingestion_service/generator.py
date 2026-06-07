"""Original, fully synthetic anime generator — NO third-party data.

Every title/synopsis/field is procedurally generated from word lists we author,
so the dataset (and any Docker image built from it) is free of copyright/licensing
concerns. Generation is deterministic: the same (seed, index) always yields the same
anime, and titles are unique for indices up to len(ADJ)*len(NOUN)^2*len(SHAPES)
(> 2 million), comfortably covering the 1M target.

Rows are produced as a stream (a generator), so 100k–1M rows never sit in memory
at once.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from dataclasses import dataclass, field

# --- word banks (authored here; expand freely) -------------------------------

ADJ = [
    "Crimson", "Azure", "Eternal", "Hollow", "Radiant", "Frozen", "Burning", "Silent",
    "Golden", "Shattered", "Velvet", "Iron", "Phantom", "Lunar", "Solar", "Verdant",
    "Obsidian", "Sacred", "Forgotten", "Boundless", "Twilight", "Savage", "Gentle",
    "Endless", "Crystal", "Scarlet", "Cobalt", "Ashen", "Emerald", "Thunderous",
    "Whispering", "Wandering", "Fearless", "Hidden", "Distant", "Restless", "Brilliant",
    "Cursed", "Blooming", "Stormbound", "Nameless", "Gilded", "Dauntless", "Serene",
    "Feral", "Luminous", "Vanishing", "Unbroken", "Starlit", "Midnight", "Crowned",
    "Wild", "Quiet", "Bright", "Fading", "Rising", "Falling", "Drifting", "Echoing",
    "Singing", "Dreaming", "Roaring", "Glimmering",
]

NOUN = [
    "Blade", "Garden", "Requiem", "Saga", "Horizon", "Empire", "Lantern", "Comet",
    "Serpent", "Academy", "Voyage", "Covenant", "Ember", "Tempest", "Sanctuary",
    "Phoenix", "Labyrinth", "Oracle", "Mirage", "Citadel", "Reverie", "Aurora",
    "Verdict", "Symphony", "Odyssey", "Paradox", "Cipher", "Bastion", "Chimera",
    "Nocturne", "Pilgrim", "Reckoning", "Spire", "Vortex", "Wanderer", "Zenith",
    "Beacon", "Cascade", "Dynasty", "Eclipse", "Fable", "Glacier", "Harbor",
    "Inferno", "Jubilee", "Keeper", "Legacy", "Monsoon", "Nexus", "Outpost",
    "Prism", "Quill", "Rampart", "Solstice", "Threshold", "Undertow", "Vigil",
    "Warden", "Specter", "Anthem", "Bloom", "Crucible", "Drifter", "Frontier",
    "Gambit", "Halcyon", "Idol", "Juggernaut", "Kestrel", "Lattice", "Maelstrom",
    "Nomad", "Overture", "Paragon", "Quasar", "Relic", "Sentinel", "Talisman",
    "Umbra", "Valkyrie", "Wyrm", "Yonder", "Zephyr", "Aegis", "Banner", "Crown",
    "Dawn", "Echo", "Flame", "Grove", "Hearth", "Ion", "Jade", "Knell", "Lotus",
    "Mantle",
]

SHAPES = [
    "{adj} {n1} of {n2}",
    "{n1}: The {adj} {n2}",
    "{adj} {n2} {n1}",
    "{n1} of the {adj} {n2}",
]

GENRES = [
    "Action", "Adventure", "Comedy", "Drama", "Fantasy", "Sci-Fi", "Slice of Life",
    "Mystery", "Romance", "Thriller", "Mecha", "Supernatural", "Sports", "Horror",
    "Psychological", "Historical", "Music", "School", "Space", "Cyberpunk",
]

STUDIO_A = [
    "Lumen", "Nova", "Kage", "Hoshi", "Sora", "Iris", "Mirai", "Aoi", "Yuki", "Tatsu",
    "Kuro", "Shiro", "Hikari", "Tsuki", "Rin", "Zen", "Aether", "Orion", "Vega", "Lyra",
]
STUDIO_B = [
    "Animation", "Studio", "Works", "Pictures", "Frames", "Lab", "House", "Forge",
    "Collective", "Atelier",
]

# synopsis fragments
_HERO = [
    "a runaway swordsmith", "an orphaned cartographer", "a disgraced pilot",
    "a reluctant heir", "a deaf violinist", "a street-magician", "a retired bounty hunter",
    "a clumsy alchemist", "a stoic lighthouse keeper", "a curious archivist",
    "a hot-headed courier", "a soft-spoken botanist", "twin storm-callers",
    "a masked duelist", "a sleepless inventor", "a wandering tea-master",
]
_SETTING = [
    "a floating archipelago", "a city built inside a glacier", "a clockwork desert",
    "a rain-soaked megacity", "a forest that remembers names", "the ruins of a sky-train",
    "a monastery above the clouds", "a neon harbor town", "a kingdom under endless dusk",
    "a station orbiting a dying star", "a valley of singing stones",
    "a school for forgotten arts",
]
_GOAL = [
    "to recover a stolen melody", "to map an impossible coastline",
    "to outrun a prophecy", "to rebuild a broken lighthouse",
    "to win a tournament of kites", "to free a trapped constellation",
    "to deliver one final letter", "to wake a sleeping garden",
    "to settle an old debt", "to find the last honest map",
]
_TWIST = [
    "but the rival they fear becomes their closest ally",
    "until a quiet betrayal changes everything",
    "while the world slowly forgets the color blue",
    "as an old machine begins to dream",
    "though the cost is measured in memories",
    "before the long night finally ends",
    "and discovers the legend was never theirs to keep",
    "while learning that mercy is its own kind of strength",
]
_STATUS = ["Finished", "Finished", "Finished", "Airing", "Upcoming"]
_EPISODES = [12, 12, 13, 24, 25, 26, 1, 50, 11, 6]


@dataclass
class AnimeRow:
    title: str
    synopsis: str
    genres: str
    score: float
    year: int
    episodes: int
    studio: str
    status: str
    combined_info: str
    metadata: dict[str, str] = field(default_factory=dict)


def _h(seed: int, i: int, salt: str) -> int:
    """Deterministic non-negative int from (seed, index, salt)."""
    digest = hashlib.blake2b(f"{seed}:{i}:{salt}".encode(), digest_size=8).digest()
    return int.from_bytes(digest, "big")


def _pick(lst: list, seed: int, i: int, salt: str):
    return lst[_h(seed, i, salt) % len(lst)]


def max_unique_titles() -> int:
    return len(ADJ) * len(NOUN) * len(NOUN) * len(SHAPES)


def _title(i: int) -> str:
    """Bijective title from index (unique for i < max_unique_titles())."""
    a = i % len(ADJ)
    rest = i // len(ADJ)
    n1 = rest % len(NOUN)
    rest //= len(NOUN)
    n2 = rest % len(NOUN)
    rest //= len(NOUN)
    shape = rest % len(SHAPES)
    if n2 == n1:  # avoid "X of X"
        n2 = (n2 + 1) % len(NOUN)
    return SHAPES[shape].format(adj=ADJ[a], n1=NOUN[n1], n2=NOUN[n2])


def generate_one(i: int, seed: int, primary_genre: str | None = None) -> AnimeRow:
    """Deterministically generate the i-th synthetic anime.

    When ``primary_genre`` is given it becomes the first (category) genre, so the
    catalog can be produced in concept-categorized batches.
    """
    title = _title(i)
    hero = _pick(_HERO, seed, i, "hero")
    setting = _pick(_SETTING, seed, i, "set")
    goal = _pick(_GOAL, seed, i, "goal")
    twist = _pick(_TWIST, seed, i, "twist")
    synopsis = (
        f"In {setting}, {hero} sets out {goal}. "
        f"What begins as a simple quest grows into something far larger — {twist}. "
        f"A story about courage, belonging, and the small choices that change a life."
    )

    # 2–3 genres, deterministic and de-duplicated; primary_genre leads when set.
    g1 = primary_genre or GENRES[_h(seed, i, "g1") % len(GENRES)]
    g2 = GENRES[_h(seed, i, "g2") % len(GENRES)]
    g3 = GENRES[_h(seed, i, "g3") % len(GENRES)]
    genres = ", ".join(dict.fromkeys([g1, g2, g3]))

    score = round(5.5 + (_h(seed, i, "score") % 420) / 100.0, 2)  # 5.50–9.69
    year = 1990 + _h(seed, i, "year") % 36                         # 1990–2025
    episodes = _EPISODES[_h(seed, i, "eps") % len(_EPISODES)]
    studio = f"{_pick(STUDIO_A, seed, i, 'sa')} {_pick(STUDIO_B, seed, i, 'sb')}"
    status = _STATUS[_h(seed, i, "status") % len(_STATUS)]
    combined_info = f"Title: {title} Overview: {synopsis} Genres: {genres}"
    return AnimeRow(
        title=title, synopsis=synopsis, genres=genres, score=score, year=year,
        episodes=episodes, studio=studio, status=status, combined_info=combined_info,
        metadata={"title": title, "genres": genres},
    )


def generate(count: int, seed: int) -> Iterator[AnimeRow]:
    """Stream ``count`` deterministic synthetic anime (memory-safe for 1M)."""
    for i in range(count):
        yield generate_one(i, seed)
