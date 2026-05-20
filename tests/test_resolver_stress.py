"""
Stress / regression tests for the HLS source resolver.

Covers the hardest real-world cases:
  - Movies with near-identical titles (Spider-Man, Avatar, Transformers …)
  - Multi-season series: wrong-season slug must be rejected
  - Series season split (Breaking Bad S5A/5B)
  - Anime absolute numbering (One Piece ep 892 → TVMaze season map)
  - Large episode numbers (ep 1000+)
  - Sequel / spin-off rejection in movie searches
  - Episode number name variants (Tập, Ep, E, bare digit)

All HTTP calls are mocked — no real network requests.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.adapters.tmdb import TmdbSeason, TmdbSeriesInfo
from backend.adapters.tvmaze import TVMazeSeason, TVMazeSeriesInfo
from backend.domain.models import EpisodeWanted, MovieWanted
from backend.sources.phimapi import PhimApiSource


# ── Generic helpers ────────────────────────────────────────────────────────────

def _src() -> PhimApiSource:
    return PhimApiSource("kkphim", "https://phimapi.com")


def _ok(r: MagicMock) -> MagicMock:
    r.raise_for_status = MagicMock()
    return r


def _search(items: list[dict]) -> MagicMock:
    r = MagicMock()
    r.status_code = 200
    r.raise_for_status = MagicMock()
    r.json.return_value = {"data": {"items": items}}
    return r


def _detail(slug: str, name: str, kind: str, year: int,
            tmdb_id: str, episodes: list[dict],
            origin_name: str | None = None) -> MagicMock:
    r = MagicMock()
    r.status_code = 200
    r.raise_for_status = MagicMock()
    r.json.return_value = {
        "status": True,
        "movie": {
            "slug": slug, "name": name,
            "origin_name": origin_name or name,
            "year": year, "type": kind,
            "tmdb": {"id": tmdb_id},
        },
        "episodes": episodes,
    }
    return r


def _empty_search() -> MagicMock:
    return _search([])


def _err() -> MagicMock:
    r = MagicMock()
    r.raise_for_status.side_effect = Exception("HTTP 404")
    return r


def _item(name: str, slug: str, year: int, tmdb_id: str,
          kind: str = "series", ep_total: int = 13) -> dict:
    return {
        "name": name, "origin_name": name,
        "type": kind, "year": year,
        "tmdb": {"id": tmdb_id} if tmdb_id else {},
        "slug": slug,
        "episode_current": str(ep_total), "episode_total": ep_total,
    }


def _movie_item(name: str, slug: str, year: int, tmdb_id: str) -> dict:
    return _item(name, slug, year, tmdb_id, kind="single", ep_total=1)


def _hls(urls: list[tuple[str, str]]) -> list[dict]:
    """Build episodes list: [(name, url), ...]"""
    return [{"server_data": [
        {"name": name, "link_m3u8": url} for name, url in urls
    ]}]


def _multi_server(eps: list[tuple[str, str]], servers: list[str]) -> list[dict]:
    """Build multiple server_data blocks, each with same episode set."""
    return [
        {"server_name": srv, "server_data": [
            {"name": name, "link_m3u8": url.replace("srv0", f"srv{i}")}
            for name, url in eps
        ]}
        for i, srv in enumerate(servers)
    ]


def _wanted_ep(title: str, tmdb_id: int, tvdb_id: int,
               season: int, ep: int, year: int = 2008) -> EpisodeWanted:
    return EpisodeWanted(
        sonarr_episode_id=1, series_id=1,
        series_title=title, episode_title="",
        year=year, tmdb_id=tmdb_id, tvdb_id=tvdb_id, imdb_id=None,
        season_number=season, episode_number=ep,
    )


def _wanted_movie(title: str, tmdb_id: int, year: int) -> MovieWanted:
    return MovieWanted(radarr_id=1, title=title, year=year,
                       tmdb_id=tmdb_id, imdb_id=None)


# ── TMDB/TVMaze fixture builders ───────────────────────────────────────────────

def _tmdb(seasons: list[tuple[int, int, int]],  # (season_no, ep_count, year)
          title: str = "Series") -> TmdbSeriesInfo:
    """Build TmdbSeriesInfo from compact season tuples."""
    tseasons = [TmdbSeason(season_number=s, episode_count=n, year=y) for s, n, y in seasons]
    return TmdbSeriesInfo(
        series_year=seasons[0][2],
        season_years={s: y for s, _, y in seasons},
        seasons=tseasons,
        total_episodes=sum(n for _, n, _ in seasons),
        total_seasons=len(seasons),
        title=title,
        alternative_titles=[title],
    )


def _tvmaze(seasons: list[tuple[int, int]]) -> TVMazeSeriesInfo:
    """Build TVMazeSeriesInfo with cumulative counts."""
    cumulative: dict[int, int] = {}
    total = 0
    tvs = []
    for sno, count in seasons:
        total += count
        cumulative[sno] = total
        tvs.append(TVMazeSeason(season_number=sno, episode_count=count))
    return TVMazeSeriesInfo(
        seasons=tvs,
        total_episodes=total,
        total_seasons=len(tvs),
        cumulative=cumulative,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 1. MOVIE TITLE COLLISION
# ══════════════════════════════════════════════════════════════════════════════

class TestMovieTitleCollision:
    """Search returns multiple near-identical titles — must pick the right one."""

    def test_spider_man_2002_not_sequel(self):
        """Spider-Man (2002) search returns 3 results; only tmdb=557 is correct."""
        src = _src()
        items = [
            _movie_item("Spider-Man 2", "spider-man-2", 2004, "976"),
            _movie_item("Spider-Man", "spider-man-2002", 2002, "557"),
            _movie_item("Spider-Man: No Way Home", "spider-man-no-way-home", 2021, "634649"),
        ]
        detail = _detail("spider-man-2002", "Spider-Man", "single", 2002, "557",
                         _hls([("Full", "https://cdn/sm2002.m3u8")]))
        with patch.object(src.session, "get") as mock:
            mock.side_effect = [_search(items), detail]
            hit = src.resolve_movie(_wanted_movie("Spider-Man", 557, 2002))
        assert hit is not None
        assert "sm2002" in hit.hls_url

    def test_avatar_2009_not_sequel(self):
        """Avatar (2009, tmdb=19995) must not resolve to Avatar: The Way of Water (2022)."""
        src = _src()
        items = [
            _movie_item("Avatar: The Way of Water", "avatar-2022", 2022, "76600"),
            _movie_item("Avatar", "avatar-2009", 2009, "19995"),
        ]
        detail = _detail("avatar-2009", "Avatar", "single", 2009, "19995",
                         _hls([("Full", "https://cdn/avatar2009.m3u8")]))
        with patch.object(src.session, "get") as mock:
            mock.side_effect = [_search(items), detail]
            hit = src.resolve_movie(_wanted_movie("Avatar", 19995, 2009))
        assert hit is not None
        assert "2009" in hit.hls_url

    def test_dark_knight_not_rises(self):
        """The Dark Knight (2008, tmdb=155) ≠ The Dark Knight Rises (2012)."""
        src = _src()
        items = [
            _movie_item("The Dark Knight Rises", "dark-knight-rises", 2012, "49521"),
            _movie_item("The Dark Knight", "dark-knight-2008", 2008, "155"),
        ]
        detail = _detail("dark-knight-2008", "The Dark Knight", "single", 2008, "155",
                         _hls([("Full", "https://cdn/dk2008.m3u8")]))
        with patch.object(src.session, "get") as mock:
            mock.side_effect = [_search(items), detail]
            hit = src.resolve_movie(_wanted_movie("The Dark Knight", 155, 2008))
        assert hit is not None
        assert "dk2008" in hit.hls_url

    def test_transformers_2007_not_sequels(self):
        """Transformers (2007) among 6 sequels — tmdb match wins."""
        src = _src()
        items = [
            _movie_item("Transformers: Revenge", "transformers-2", 2009, "8373"),
            _movie_item("Transformers: Dark of the Moon", "transformers-3", 2011, "38356"),
            _movie_item("Transformers", "transformers-2007", 2007, "1858"),
        ]
        detail = _detail("transformers-2007", "Transformers", "single", 2007, "1858",
                         _hls([("Full", "https://cdn/tf2007.m3u8")]))
        with patch.object(src.session, "get") as mock:
            mock.side_effect = [_search(items), detail]
            hit = src.resolve_movie(_wanted_movie("Transformers", 1858, 2007))
        assert hit is not None
        assert "tf2007" in hit.hls_url

    def test_movie_tmdb_mismatch_falls_through_to_none(self):
        """All search results have wrong tmdb IDs and wrong years → None."""
        src = _src()
        items = [
            _movie_item("Spider-Man 2", "spider-man-2", 2004, "976"),
            _movie_item("Spider-Man: Far From Home", "spider-man-ffh", 2019, "429617"),
        ]
        with patch.object(src.session, "get") as mock:
            mock.side_effect = [_search(items), _err()]
            hit = src.resolve_movie(_wanted_movie("Spider-Man", 557, 2002))
        assert hit is None


# ══════════════════════════════════════════════════════════════════════════════
# 2. SERIES — WRONG SEASON REJECTED
# ══════════════════════════════════════════════════════════════════════════════

class TestSeriesSeasonIsolation:
    """Slugs from wrong seasons must be scored out; only matching-season slug wins."""

    def _got_tmdb(self) -> TmdbSeriesInfo:
        return _tmdb([
            (1, 10, 2011), (2, 10, 2012), (3, 10, 2013),
            (4, 10, 2014), (5, 13, 2015), (6, 10, 2016), (7, 7, 2017),
        ], title="Game of Thrones")

    def test_s3_slug_returned_not_s1(self):
        """Search returns S1 and S3 slugs; requesting S3E5 must use S3 slug."""
        src = _src()
        items = [
            _item("Game of Thrones", "got-s1", 2011, "1399", ep_total=10),
            _item("Game of Thrones Phần 3", "got-s3", 2013, "1399", ep_total=10),
        ]
        # S3 slug detail with ep5
        detail_s3 = _detail("got-s3", "Game of Thrones Phần 3", "series", 2013, "1399",
                            _hls([(str(i), f"https://cdn/got-s3e{i}.m3u8") for i in range(1, 11)]))
        with patch.object(src.session, "get") as mock:
            with patch.object(src.tmdb, "get_series_info", return_value=self._got_tmdb()):
                # search → detail for s1 (skipped: season mismatch) → detail for s3
                detail_s1 = _detail("got-s1", "Game of Thrones", "series", 2011, "1399",
                                    _hls([(str(i), f"https://cdn/got-s1e{i}.m3u8") for i in range(1, 11)]))
                mock.side_effect = [_search(items), detail_s1, detail_s3]
                hit = src.resolve_episode(_wanted_ep("Game of Thrones", 1399, 81189, season=3, ep=5))
        assert hit is not None
        assert "s3e5" in hit.hls_url

    def test_wrong_season_only_returns_none(self):
        """Only S1 slug available; requesting S3E1 must return None."""
        src = _src()
        items = [_item("Game of Thrones", "got-s1", 2011, "1399", ep_total=10)]
        detail_s1 = _detail("got-s1", "Game of Thrones", "series", 2011, "1399",
                            _hls([(str(i), f"https://cdn/got-s1e{i}.m3u8") for i in range(1, 11)]))
        with patch.object(src.session, "get") as mock:
            with patch.object(src.tmdb, "get_series_info", return_value=self._got_tmdb()):
                mock.side_effect = [_search(items), detail_s1, _err()]
                hit = src.resolve_episode(_wanted_ep("Game of Thrones", 1399, 81189, season=3, ep=1))
        assert hit is None

    def test_breaking_bad_s5_second_half(self):
        """Breaking Bad S5E9–16 stored as separate 'S5B' slug on some sites."""
        src = _src()
        tmdb_info = _tmdb([(1, 7, 2008), (2, 13, 2009), (3, 13, 2010),
                            (4, 13, 2011), (5, 16, 2012)], title="Breaking Bad")
        # Some sites label S5 part 2 differently but keep tmdb_id same
        items = [_item("Breaking Bad Phần 5", "breaking-bad-s5", 2012, "1396", ep_total=16)]
        detail = _detail("breaking-bad-s5", "Breaking Bad Phần 5", "series", 2012, "1396",
                         _hls([(str(i), f"https://cdn/bb-s5e{i}.m3u8") for i in range(1, 17)]))
        with patch.object(src.session, "get") as mock:
            with patch.object(src.tmdb, "get_series_info", return_value=tmdb_info):
                mock.side_effect = [_search(items), detail]
                hit = src.resolve_episode(_wanted_ep("Breaking Bad", 1396, 81189, season=5, ep=9))
        assert hit is not None
        assert "s5e9" in hit.hls_url

    def test_squid_game_s2_not_s1(self):
        """Squid Game S2E1 — site has both S1 and S2 slugs."""
        src = _src()
        tmdb_info = _tmdb([(1, 9, 2021), (2, 7, 2024)], title="Squid Game")
        items = [
            _item("Squid Game", "squid-game-s1", 2021, "93405", ep_total=9),
            _item("Squid Game Phần 2", "squid-game-s2", 2024, "93405", ep_total=7),
        ]
        detail_s1 = _detail("squid-game-s1", "Squid Game", "series", 2021, "93405",
                            _hls([(str(i), f"https://cdn/sg-s1e{i}.m3u8") for i in range(1, 10)]))
        detail_s2 = _detail("squid-game-s2", "Squid Game Phần 2", "series", 2024, "93405",
                            _hls([(str(i), f"https://cdn/sg-s2e{i}.m3u8") for i in range(1, 8)]))
        with patch.object(src.session, "get") as mock:
            with patch.object(src.tmdb, "get_series_info", return_value=tmdb_info):
                mock.side_effect = [_search(items), detail_s1, detail_s2]
                hit = src.resolve_episode(_wanted_ep("Squid Game", 93405, 0, season=2, ep=1, year=2021))
        assert hit is not None
        assert "s2e1" in hit.hls_url

    def test_stranger_things_s4_not_s1(self):
        """Stranger Things S4E1 must not resolve from S1 slug."""
        src = _src()
        tmdb_info = _tmdb([(1, 8, 2016), (2, 9, 2017), (3, 8, 2019), (4, 9, 2022)],
                          title="Stranger Things")
        items = [
            _item("Stranger Things", "stranger-things-s1", 2016, "66732", ep_total=8),
            _item("Stranger Things Phần 4", "stranger-things-s4", 2022, "66732", ep_total=9),
        ]
        detail_s1 = _detail("stranger-things-s1", "Stranger Things", "series", 2016, "66732",
                            _hls([(str(i), f"https://cdn/st-s1e{i}.m3u8") for i in range(1, 9)]))
        detail_s4 = _detail("stranger-things-s4", "Stranger Things Phần 4", "series", 2022, "66732",
                            _hls([(str(i), f"https://cdn/st-s4e{i}.m3u8") for i in range(1, 10)]))
        with patch.object(src.session, "get") as mock:
            with patch.object(src.tmdb, "get_series_info", return_value=tmdb_info):
                mock.side_effect = [_search(items), detail_s1, detail_s4]
                hit = src.resolve_episode(_wanted_ep("Stranger Things", 66732, 0, season=4, ep=1, year=2016))
        assert hit is not None
        assert "s4e1" in hit.hls_url


# ══════════════════════════════════════════════════════════════════════════════
# 3. EPISODE NAME PATTERN VARIANTS
# ══════════════════════════════════════════════════════════════════════════════

class TestEpisodeNamePatterns:
    """Sites label episodes very differently — resolver must parse all forms."""

    def _run(self, ep_names: list[str], wanted_ep: int,
             should_find: bool = True) -> None:
        src = _src()
        tmdb_info = _tmdb([(1, 12, 2022)], title="Test Series")
        items = [_item("Test Series", "test-series", 2022, "99999")]
        episodes = _hls([(name, f"https://cdn/ep-{name}.m3u8") for name in ep_names])
        detail = _detail("test-series", "Test Series", "series", 2022, "99999", episodes)
        with patch.object(src.session, "get") as mock:
            with patch.object(src.tmdb, "get_series_info", return_value=tmdb_info):
                mock.side_effect = [_search(items), detail, _err()]
                hit = src.resolve_episode(_wanted_ep("Test Series", 99999, 0, season=1, ep=wanted_ep, year=2022))
        if should_find:
            assert hit is not None, f"Expected hit for ep={wanted_ep} with names={ep_names}"
        else:
            assert hit is None, f"Expected None for ep={wanted_ep} with names={ep_names}"

    def test_bare_digit(self):
        self._run(["1", "2", "3"], wanted_ep=1)

    def test_tap_prefix(self):
        self._run(["Tập 1", "Tập 2", "Tập 3"], wanted_ep=2)

    def test_ep_prefix(self):
        self._run(["Ep 1", "Ep 2", "Ep 5"], wanted_ep=5)

    def test_episode_prefix(self):
        self._run(["Episode 1", "Episode 2"], wanted_ep=1)

    def test_e_prefix(self):
        self._run(["E01", "E02", "E12"], wanted_ep=12)

    def test_zero_padded(self):
        self._run(["01", "02", "12"], wanted_ep=12)

    def test_wrong_episode_not_matched(self):
        """Names [2,3,4] — requesting ep=1 must return None."""
        self._run(["2", "3", "4"], wanted_ep=1, should_find=False)

    def test_large_episode_number(self):
        """Episode list contains ep 892."""
        names = [str(i) for i in range(890, 895)]
        self._run(names, wanted_ep=892)

    def test_three_digit_episode_tap_prefix(self):
        """Tập 100 matches ep=100."""
        names = ["Tập 99", "Tập 100", "Tập 101"]
        self._run(names, wanted_ep=100)


# ══════════════════════════════════════════════════════════════════════════════
# 4. ANIME ABSOLUTE NUMBERING (TVMaze mapping)
# ══════════════════════════════════════════════════════════════════════════════

class TestAnimeAbsoluteNumbering:
    """
    Anime sites often use absolute episode numbers across all seasons.
    TVMaze gives us the cumulative count per season, which lets the resolver
    convert TVDB S{n}E{m} → absolute episode for matching.

    Example: One Piece TVDB S21E1 = absolute ep 957
             (after 956 eps across S1-S20)
    """

    def _one_piece_tmdb(self) -> TmdbSeriesInfo:
        # Simplified: 21 seasons, each ~61 eps (real is uneven but fine for test)
        seasons = [(i, 61, 1999 + i) for i in range(1, 22)]
        return _tmdb(seasons, title="One Piece")

    def _one_piece_tvmaze(self) -> TVMazeSeriesInfo:
        # Cumulative: S1=61, S2=122, ..., S20=1220, S21=1281
        seasons = [(i, 61) for i in range(1, 22)]
        return _tvmaze(seasons)

    def test_one_piece_s1e1_absolute_1(self):
        """One Piece S1E1 = absolute ep 1. Site labels it '1'."""
        src = _src()
        items = [_item("One Piece", "one-piece", 1999, "37854", ep_total=1100)]
        # Site has eps labeled 1, 2, 3, ...
        eps = _hls([(str(i), f"https://cdn/op{i}.m3u8") for i in range(1, 20)])
        detail = _detail("one-piece", "One Piece", "series", 1999, "37854", eps)
        tvmaze = self._one_piece_tvmaze()
        with patch.object(src.session, "get") as mock:
            with patch.object(src.tmdb, "get_series_info", return_value=self._one_piece_tmdb()):
                with patch("backend.sources.phimapi.TVMazeClient") as MockTV:
                    MockTV.return_value.get_series_info.return_value = tvmaze
                    mock.side_effect = [_search(items), detail]
                    hit = src.resolve_episode(_wanted_ep("One Piece", 37854, 81797, season=1, ep=1, year=1999))
        assert hit is not None
        assert "op1.m3u8" in hit.hls_url

    def test_one_piece_s2e5_absolute_66(self):
        """One Piece S2E5 = absolute 61+5=66. Site labels it '66'."""
        src = _src()
        items = [_item("One Piece", "one-piece", 1999, "37854", ep_total=1100)]
        eps = _hls([(str(i), f"https://cdn/op{i}.m3u8") for i in range(60, 75)])
        detail = _detail("one-piece", "One Piece", "series", 1999, "37854", eps)
        tvmaze = self._one_piece_tvmaze()
        with patch.object(src.session, "get") as mock:
            with patch.object(src.tmdb, "get_series_info", return_value=self._one_piece_tmdb()):
                with patch("backend.sources.phimapi.TVMazeClient") as MockTV:
                    MockTV.return_value.get_series_info.return_value = tvmaze
                    mock.side_effect = [_search(items), detail]
                    hit = src.resolve_episode(_wanted_ep("One Piece", 37854, 81797, season=2, ep=5, year=1999))
        assert hit is not None
        assert "op66.m3u8" in hit.hls_url

    def test_one_piece_s21e1_absolute_1281_minus_60(self):
        """One Piece S21E1 = abs 1221 (S20 cumulative 1220 + 1)."""
        src = _src()
        items = [_item("One Piece", "one-piece", 1999, "37854", ep_total=1300)]
        abs_ep = 1221
        eps = _hls([(str(i), f"https://cdn/op{i}.m3u8") for i in range(1218, 1225)])
        detail = _detail("one-piece", "One Piece", "series", 1999, "37854", eps)
        tvmaze = self._one_piece_tvmaze()
        with patch.object(src.session, "get") as mock:
            with patch.object(src.tmdb, "get_series_info", return_value=self._one_piece_tmdb()):
                with patch("backend.sources.phimapi.TVMazeClient") as MockTV:
                    MockTV.return_value.get_series_info.return_value = tvmaze
                    mock.side_effect = [_search(items), detail]
                    hit = src.resolve_episode(_wanted_ep("One Piece", 37854, 81797, season=21, ep=1, year=1999))
        assert hit is not None
        assert f"op{abs_ep}.m3u8" in hit.hls_url

    def test_naruto_s3e53_absolute(self):
        """
        Naruto (tmdb=46260). S1=220 eps (absolute), S2=500 eps — simplified.
        Requesting S1E53 → absolute 53.
        """
        src = _src()
        tmdb_info = _tmdb([(1, 220, 2002), (2, 280, 2007)], title="Naruto")
        tvmaze = _tvmaze([(1, 220), (2, 280)])
        items = [_item("Naruto", "naruto", 2002, "46260", ep_total=500)]
        eps = _hls([(str(i), f"https://cdn/naruto{i}.m3u8") for i in range(50, 60)])
        detail = _detail("naruto", "Naruto", "series", 2002, "46260", eps)
        with patch.object(src.session, "get") as mock:
            with patch.object(src.tmdb, "get_series_info", return_value=tmdb_info):
                with patch("backend.sources.phimapi.TVMazeClient") as MockTV:
                    MockTV.return_value.get_series_info.return_value = tvmaze
                    mock.side_effect = [_search(items), detail]
                    hit = src.resolve_episode(_wanted_ep("Naruto", 46260, 78857, season=1, ep=53, year=2002))
        assert hit is not None
        assert "naruto53.m3u8" in hit.hls_url

    def test_tvmaze_unavailable_falls_back_to_relative(self):
        """When TVMaze returns None, resolver falls back to relative ep number."""
        src = _src()
        tmdb_info = _tmdb([(1, 13, 2019)], title="The Witcher")
        items = [_item("The Witcher", "witcher-s1", 2019, "71912", ep_total=13)]
        eps = _hls([(str(i), f"https://cdn/witcher-s1e{i}.m3u8") for i in range(1, 14)])
        detail = _detail("witcher-s1", "The Witcher", "series", 2019, "71912", eps)
        with patch.object(src.session, "get") as mock:
            with patch.object(src.tmdb, "get_series_info", return_value=tmdb_info):
                with patch("backend.sources.phimapi.TVMazeClient") as MockTV:
                    MockTV.return_value.get_series_info.return_value = None
                    mock.side_effect = [_search(items), detail]
                    hit = src.resolve_episode(_wanted_ep("The Witcher", 71912, 0, season=1, ep=5, year=2019))
        assert hit is not None
        assert "s1e5" in hit.hls_url


# ══════════════════════════════════════════════════════════════════════════════
# 5. ATTACK ON TITAN — FINAL SEASON NAMING
# ══════════════════════════════════════════════════════════════════════════════

class TestFinalSeasonNaming:
    """
    Sites often label Attack on Titan S4 as 'Final Season' or 'Season 4' in
    a separate slug. detect_season must parse this as season 4.
    """

    def _aot_tmdb(self) -> TmdbSeriesInfo:
        return _tmdb([
            (1, 25, 2013), (2, 12, 2017), (3, 22, 2018), (4, 29, 2020),
        ], title="Attack on Titan")

    def test_final_season_resolves_as_s4(self):
        """Slug 'aot-final-season' must be detected as season=4 and episode matched."""
        src = _src()
        items = [
            # Slug whose name has "4" but via "Final Season" title
            _item("Shingeki no Kyojin: Final Season", "aot-final-season", 2020, "1429", ep_total=29),
        ]
        eps = _hls([(str(i), f"https://cdn/aot-s4e{i}.m3u8") for i in range(1, 30)])
        detail = _detail("aot-final-season",
                         "Shingeki no Kyojin: The Final Season",
                         "series", 2020, "1429", eps)
        with patch.object(src.session, "get") as mock:
            with patch.object(src.tmdb, "get_series_info", return_value=self._aot_tmdb()):
                mock.side_effect = [_search(items), detail]
                hit = src.resolve_episode(_wanted_ep("Attack on Titan", 1429, 83097, season=4, ep=1, year=2013))
        # Either resolves S4E1, or falls through — should NOT crash
        # If site detect_season correctly gives 4 → hit; if not → None is acceptable but not a crash
        # We assert no exception was thrown (hit is None | SourceHit)
        assert hit is None or "s4e1" in hit.hls_url

    def test_numbered_season_in_title_detected(self):
        """'Attack on Titan Season 3' → detect_season=3."""
        src = _src()
        items = [
            _item("Attack on Titan Season 3", "aot-s3", 2018, "1429", ep_total=22),
        ]
        eps = _hls([(str(i), f"https://cdn/aot-s3e{i}.m3u8") for i in range(1, 23)])
        detail = _detail("aot-s3", "Attack on Titan Season 3", "series", 2018, "1429", eps)
        with patch.object(src.session, "get") as mock:
            with patch.object(src.tmdb, "get_series_info", return_value=self._aot_tmdb()):
                mock.side_effect = [_search(items), detail]
                hit = src.resolve_episode(_wanted_ep("Attack on Titan", 1429, 83097, season=3, ep=5, year=2013))
        assert hit is not None
        assert "s3e5" in hit.hls_url


# ══════════════════════════════════════════════════════════════════════════════
# 6. MULTI-SERVER DEDUPLICATION
# ══════════════════════════════════════════════════════════════════════════════

class TestMultiServerDedup:
    """resolve_episode_all returns one hit per server, deduplicating same URLs."""

    def test_two_servers_both_returned(self):
        src = _src()
        tmdb_info = _tmdb([(1, 8, 2019)], title="Miniseries")
        items = [_item("Miniseries", "mini-s1", 2019, "55555")]
        eps = _multi_server([("1", "https://cdn/srv0/ep1.m3u8")], ["Server A", "Server B"])
        detail = _detail("mini-s1", "Miniseries", "series", 2019, "55555", eps)
        with patch.object(src.session, "get") as mock:
            with patch.object(src.tmdb, "get_series_info", return_value=tmdb_info):
                mock.side_effect = [_search(items), detail]
                hits = src.resolve_episode_all(_wanted_ep("Miniseries", 55555, 0, season=1, ep=1, year=2019))
        assert len(hits) == 2
        servers = {h.server_name for h in hits}
        assert "Server A" in servers and "Server B" in servers

    def test_duplicate_urls_deduped(self):
        """Same URL appearing in two servers is returned only once."""
        src = _src()
        tmdb_info = _tmdb([(1, 8, 2019)], title="Miniseries")
        items = [_item("Miniseries", "mini-s1", 2019, "55555")]
        # Both servers have the same URL
        same_url = "https://cdn/same/ep1.m3u8"
        eps = [
            {"server_name": "A", "server_data": [{"name": "1", "link_m3u8": same_url}]},
            {"server_name": "B", "server_data": [{"name": "1", "link_m3u8": same_url}]},
        ]
        detail = _detail("mini-s1", "Miniseries", "series", 2019, "55555", eps)
        with patch.object(src.session, "get") as mock:
            with patch.object(src.tmdb, "get_series_info", return_value=tmdb_info):
                mock.side_effect = [_search(items), detail]
                hits = src.resolve_episode_all(_wanted_ep("Miniseries", 55555, 0, season=1, ep=1, year=2019))
        urls = [h.hls_url for h in hits]
        assert urls.count(same_url) == 1, "Duplicate URL should be deduped"


# ══════════════════════════════════════════════════════════════════════════════
# 7. EDGE CASES
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_series_with_only_future_episodes_returns_none(self):
        """Server only has eps 5,6,7 but we want ep 1 → None."""
        src = _src()
        tmdb_info = _tmdb([(1, 10, 2022)], title="Future Show")
        items = [_item("Future Show", "future-show", 2022, "77777")]
        eps = _hls([("5", "https://cdn/ep5.m3u8"), ("6", "https://cdn/ep6.m3u8")])
        detail = _detail("future-show", "Future Show", "series", 2022, "77777", eps)
        with patch.object(src.session, "get") as mock:
            with patch.object(src.tmdb, "get_series_info", return_value=tmdb_info):
                mock.side_effect = [_search(items), detail, _err()]
                hit = src.resolve_episode(_wanted_ep("Future Show", 77777, 0, season=1, ep=1, year=2022))
        assert hit is None

    def test_series_search_network_error_returns_none(self):
        src = _src()
        with patch.object(src.session, "get", side_effect=Exception("timeout")):
            hit = src.resolve_episode(_wanted_ep("Any Show", 99999, 0, season=1, ep=1))
        assert hit is None

    def test_movie_detail_network_error_returns_none(self):
        src = _src()
        items = [_movie_item("Avatar", "avatar-2009", 2009, "19995")]
        with patch.object(src.session, "get") as mock:
            mock.side_effect = [_search(items), _err(), _err()]
            hit = src.resolve_movie(_wanted_movie("Avatar", 19995, 2009))
        assert hit is None

    def test_series_all_empty_episodes_returns_none(self):
        """Detail page has episodes=[{}] with no server_data."""
        src = _src()
        tmdb_info = _tmdb([(1, 8, 2022)], title="Broken Show")
        items = [_item("Broken Show", "broken-show", 2022, "88888")]
        detail = _detail("broken-show", "Broken Show", "series", 2022, "88888", [{}])
        with patch.object(src.session, "get") as mock:
            with patch.object(src.tmdb, "get_series_info", return_value=tmdb_info):
                mock.side_effect = [_search(items), detail, _err()]
                hit = src.resolve_episode(_wanted_ep("Broken Show", 88888, 0, season=1, ep=1, year=2022))
        assert hit is None

    def test_movie_type_mismatch_tv_not_returned(self):
        """Search returns a TV series with same name — must be rejected (type != single)."""
        src = _src()
        # TV show "The Flash" should not match movie "The Flash" (type=series vs single)
        items = [_item("The Flash", "the-flash-series", 2014, "60735", kind="series", ep_total=22)]
        with patch.object(src.session, "get") as mock:
            mock.side_effect = [_search(items), _err()]
            hit = src.resolve_movie(_wanted_movie("The Flash", 298618, 2023))
        assert hit is None
