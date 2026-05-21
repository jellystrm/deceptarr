from __future__ import annotations

from backend.adapters.media_managers import RadarrClient, SonarrClient


class TestArrTitleFallbacks:
    def test_radarr_missing_title_falls_back_to_tmdb_id(self):
        client = RadarrClient("http://radarr", "key")
        client.get = lambda *args, **kwargs: {
            "records": [{"movie": {"id": 10, "tmdbId": 24428, "imdbId": "tt0848228"}}]
        }

        [movie] = client.missing_movies(1)

        assert movie.title == "TMDB 24428"

    def test_sonarr_missing_series_title_falls_back_to_tvdb_id(self):
        client = SonarrClient("http://sonarr", "key")
        client.get = lambda *args, **kwargs: {
            "records": [
                {
                    "id": 99,
                    "seriesId": 12,
                    "seasonNumber": 1,
                    "episodeNumber": 1,
                    "series": {"tvdbId": 81189},
                }
            ]
        }

        [episode] = client.missing_episodes(1)

        assert episode.series_title == "TVDB 81189"
