from typing import Protocol, TypedDict, NotRequired

class NormalizedGame(TypedDict):
    """
    Normalized game data structure returned by all store integrations.

    Required fields:
        appid: Platform-specific game identifier
        name: Game title
        notion_store_id: Notion page ID for store relation

    Optional fields (include to skip IGDB API calls):
        platforms: List of platform names (e.g., ['PC (Microsoft Windows)', 'Mac'])
        cover_url: Direct URL to cover image
        release_date: Release date in YYYY-MM-DD format
        genres: List of genre names (e.g., ['Action', 'Adventure'])
        game_modes: List of game modes (e.g., ['Single player', 'Multiplayer'])
        achievement_percentage: Achievement completion percentage (0-100)
        last_played: Last played date in YYYY-MM-DD format
        status: Game status (Currently Playing, Backlog, Complete, On Hold, Abandoned)
    """
    appid: int | str
    name: str
    notion_store_id: str
    platforms: NotRequired[list[str]]
    cover_url: NotRequired[str]
    release_date: NotRequired[str]
    genres: NotRequired[list[str]]
    game_modes: NotRequired[list[str]]
    achievement_percentage: NotRequired[float]
    last_played: NotRequired[str]
    status: NotRequired[str]

class StoreIntegrationProtocol(Protocol):
    """
    Protocol that all store integrations must implement.

    Each integration should:
    1. Fetch games from the store's API
    2. Extract all available metadata
    3. Return normalized data in NormalizedGame format

    The normalization happens INSIDE the integration, not after.
    This allows each store to optimize data extraction and reduce external API calls.
    """

    def get_owned_games(self) -> list[NormalizedGame]:
        """
        Fetch all owned games and return them in normalized format.

        This method should:
        - Fetch games from the store's API
        - Extract all available metadata (platforms, cover, release date, genres, etc.)
        - Return a list of NormalizedGame dictionaries

        Returns:
            List of normalized game dictionaries with all available metadata
        """
        ...