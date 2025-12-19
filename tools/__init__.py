# Game Recommendation Agent Tools
from .metacritic import (
    search_games,
    get_game_details,
    get_top_games_by_platform,
    get_recent_releases,
)

__all__ = [
    "search_games",
    "get_game_details", 
    "get_top_games_by_platform",
    "get_recent_releases",
]
