from __future__ import annotations

from abc import ABC, abstractmethod

from deceptarr.domain.models import EpisodeWanted, MovieWanted, SourceHit


class Source(ABC):
    name: str

    @abstractmethod
    def resolve_movie(self, movie: MovieWanted) -> SourceHit | None:
        raise NotImplementedError

    @abstractmethod
    def resolve_episode(self, episode: EpisodeWanted) -> SourceHit | None:
        raise NotImplementedError

    def resolve_movie_all(self, movie: MovieWanted) -> list[SourceHit]:
        hit = self.resolve_movie(movie)
        return [hit] if hit else []

    def resolve_episode_all(self, episode: EpisodeWanted) -> list[SourceHit]:
        hit = self.resolve_episode(episode)
        return [hit] if hit else []
