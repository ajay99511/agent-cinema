"""Curated corpus film list (Slice 2 / Q1, Q3 resolution).

Q1 (dataset): rather than a pre-parsed academic corpus (ScriptBase/ScreenPy — unclear
redistribution terms, and ScreenPy is a parsing tool, not a dataset), we fetch raw text
directly from IMSDb ourselves and parse it with our own lightweight scene-heading splitter
(parse_script.py). IMSDb's own terms frame the scripts as available for reading/research;
we never store or redistribute the screenplay text itself — only derived features (VAD
scores, embeddings, short scene headings, a model-generated one-line summary) end up in
ClickHouse. Each title below was empirically checked to have a healthy count of real
INT./EXT. sluglines before being added (loose transcript-style pages without them, e.g.
early builds tried "Fargo", were rejected — see PROGRESS.md Slice 2 log).

Q3 (corpus N): descoped from the plan's 100-150 to ~25 given the 7-day timeline discovered
in Session 5. Genre buckets are uneven (crime/sci-fi/drama dominate; action=1, horror=2
titles) — this is a known thinness risk for cohorts in those two genres. The plan's own
N>=min invariant (default 20, at the *scene* level, not film level) is the designed
mitigation: thin cohorts degrade to an honest "insufficient corpus" rather than a fake
percentile. Revisit if time allows — adding a handful more action/horror titles is cheap
now that the pipeline exists.
"""

from __future__ import annotations

from dataclasses import dataclass

_BASE_URL = "https://imsdb.com/scripts/{slug}.html"


@dataclass(frozen=True)
class FilmSpec:
    script_id: int
    title: str
    year: int
    genre: str
    slug: str  # IMSDb URL slug, e.g. "Se7en" -> https://imsdb.com/scripts/Se7en.html

    @property
    def url(self) -> str:
        return _BASE_URL.format(slug=self.slug)


# script_id starts at 100 to never collide with Slice 1's placeholder seed (script_id=1,
# is_corpus=1) — that row gets deleted once this real corpus is loaded (see run.py).
FILMS: list[FilmSpec] = [
    FilmSpec(100, "American Beauty", 1999, "drama", "American-Beauty"),
    FilmSpec(101, "Blade Runner", 1982, "scifi", "Blade-Runner"),
    FilmSpec(102, "The Departed", 2006, "crime", "Departed,-The"),
    FilmSpec(103, "Erin Brockovich", 2000, "drama", "Erin-Brockovich"),
    FilmSpec(104, "Fight Club", 1999, "drama", "Fight-Club"),
    FilmSpec(105, "Gladiator", 2000, "action", "Gladiator"),
    FilmSpec(106, "The Godfather", 1972, "crime", "Godfather"),
    FilmSpec(107, "Good Will Hunting", 1997, "drama", "Good-Will-Hunting"),
    FilmSpec(108, "Groundhog Day", 1993, "comedy", "Groundhog-Day"),
    FilmSpec(109, "Inception", 2010, "scifi", "Inception"),
    FilmSpec(110, "Jurassic Park", 1993, "scifi", "Jurassic-Park"),
    FilmSpec(111, "Se7en", 1995, "crime", "Se7en"),
    FilmSpec(112, "The Sixth Sense", 1999, "horror", "Sixth-Sense,-The"),
    FilmSpec(113, "Aliens", 1986, "scifi", "Aliens"),
    FilmSpec(114, "American History X", 1998, "drama", "American-History-X"),
    FilmSpec(115, "Ex Machina", 2014, "scifi", "Ex-Machina"),
    FilmSpec(116, "Get Out", 2017, "horror", "Get-Out"),
    FilmSpec(117, "Heat", 1995, "crime", "Heat"),
    FilmSpec(118, "Juno", 2007, "comedy", "Juno"),
    FilmSpec(119, "L.A. Confidential", 1997, "crime", "L.A.-Confidential"),
    FilmSpec(120, "The Matrix", 1999, "scifi", "Matrix,-The"),
    FilmSpec(121, "No Country for Old Men", 2007, "crime", "No-Country-for-Old-Men"),
    FilmSpec(122, "Pulp Fiction", 1994, "crime", "Pulp-Fiction"),
    FilmSpec(123, "The Social Network", 2010, "drama", "Social-Network,-The"),
    FilmSpec(124, "Superbad", 2007, "comedy", "Superbad"),
]
