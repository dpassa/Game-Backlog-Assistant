from typing import Protocol

class StoreIntegrationProtocol(Protocol):
    def store(self, data: str) -> None:
        # This method is intentionally left empty as it is meant to be implemented by subclasses.
        pass

    def get_owned_games(self) -> list:
        # This method is intentionally left empty as it is meant to be implemented by subclasses.
        pass

    def get_game_info(self, appid: int) -> dict:
        # This method is intentionally left empty as it is meant to be implemented by subclasses.
        pass