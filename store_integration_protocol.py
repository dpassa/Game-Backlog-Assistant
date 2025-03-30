from typing import Protocol

class StoreIntegrationProtocol(Protocol):
    def store(self, data: str) -> None:
        pass

    def get_owned_games(self) -> list:
        pass

    def get_game_info(self, appid: int) -> dict:
        pass