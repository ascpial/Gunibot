from __future__ import annotations
import json
from typing import Any, Dict, List, Optional

import nextcord

__all__ = [
    "Configuration"
]


class Configuration:
    def __init__(self, path: str = "configuration.json") -> None:
        self.path = path
        self.load()
    
    def load(self) -> Configuration:
        with open(self.path, 'r') as configuration_file:
            self._raw_config: Dict[str, Dict[str, Any]] = json.load(
                configuration_file
            )

    @property
    def token(self) -> str:
        return self._raw_config['discord']['token']

    @property
    def prefix(self) -> str:
        return self._raw_config['discord'].get('prefix', '!')

    @property
    def description(self) -> str:
        return self._raw_config['discord'].get('description')

    @property
    def guild_ids(self) -> List[int]:
        return self._raw_config['discord'].get('guild_ids', [])

    @property
    def database_path(self) -> str:
        return self._raw_config.get('database', {}).get('path', 'database.db')
    
    @property
    def database_type(self) -> str:
        return self._raw_config.get('database', {}).get('type', 'sqlite')
    
    @property
    def database_location(self) -> str:
        return self._raw_config.get('database', {}).get('location', '')

    def add_guilds(self, command: nextcord.ApplicationCommand) -> nextcord.ApplicationCommand:
        for guild_id in self.guild_ids:
            command.add_guild_rollout(guild_id)