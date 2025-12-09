import configparser
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import ClassVar

from growbies.constants import APPNAME
from growbies.utils.paths import InstallPaths


@dataclass
class Account:
    """Account configuration."""
    name: str = 'Default'


@dataclass
class Database:
    """Database configuration."""
    address: str = ''

@dataclass
class Gateway:
    """Gateway configuration."""
    name: str = 'Default'


@dataclass
class Cfg:
    class Section(StrEnum):
        ACCOUNT = 'account'
        DATABASE = 'database'
        GATEWAY = 'gateway'

    class AccountSectionKey(StrEnum):
        NAME = 'name'

    class DatabaseSectionKey(StrEnum):
        ADDRESS = 'address'

    class GatewaySectionKey(StrEnum):
        NAME = 'name'

    account: Account = field(default_factory=Account)
    database: Database = field(default_factory=Database)
    gateway: Gateway = field(default_factory=Gateway)

    PATH: ClassVar[Path] = InstallPaths.ETC_GROWBIES_CFG.value

    def __post_init__(self):
        """Load configuration from file automatically on construction."""
        if self.PATH.exists():
            cfg = configparser.ConfigParser()
            cfg.read(self.PATH)

            self.account.name = cfg.get(self.Section.ACCOUNT, self.AccountSectionKey.NAME,
                                        fallback=self.account.name)
            self.database.address = cfg.get(self.Section.DATABASE, self.DatabaseSectionKey.ADDRESS,
                                            fallback=self.database.address)
            self.gateway.name = cfg.get(self.Section.GATEWAY, self.GatewaySectionKey.NAME,
                                        fallback=self.gateway.name)

    def save(self):
        self.PATH.parent.mkdir(parents=True, exist_ok=True)
        cfg = configparser.ConfigParser()

        cfg[self.Section.ACCOUNT] = {self.AccountSectionKey.NAME: self.account.name}
        cfg[self.Section.DATABASE] = {self.DatabaseSectionKey.ADDRESS: self.database.address}
        cfg[self.Section.GATEWAY] = {self.GatewaySectionKey.NAME: self.gateway.name}

        with open(self.PATH, 'w') as f:
            cfg.write(f)

    def __str__(self):
        parts = [f"# {APPNAME.capitalize()} configuration.\n",
                 f"[{self.Section.ACCOUNT}]\n{self.AccountSectionKey.NAME} = {self.account.name}\n",
                 f"[{self.Section.DATABASE}]\n{self.DatabaseSectionKey.ADDRESS} = "
                 f"{self.database.address}\n",
                 f"[{self.Section.GATEWAY}]\n{self.GatewaySectionKey.NAME} = {self.gateway.name}\n"]
        return ''.join(parts)

_cfg = None
def get_cfg() -> Cfg:
    global _cfg
    if _cfg is None:
        _cfg = Cfg()
    return _cfg