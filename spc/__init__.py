"""
SulvionPiCord (SPC)
~~~~~~~~~~~~~~~~~~

An easy and powerful Discord bot wrapper built on top of discord.py.
Designed for simplicity, efficiency, and rapid development.

:copyright: (c) 2025 Hafiz Daffa W
:license: MIT, see LICENSE for more details.
"""

__title__ = "spc"
__author__ = "Hafiz Daffa W"
__license__ = "MIT"
__copyright__ = "Copyright 2025 Hafiz Daffa W"
__version__ = "0.1.2"

from .bot import Bot, initBot
from .objects import Context, SyncContext, Embed, Button, Sender
from .database import Database
from .const import (
    NOPREFIX,
    HIDDEN,
    REPEATABLE,
    AUTOARGS,
    SLASH,
    ONCE,
    BACKGROUND,
    LOGGED,
    DEL_BEFORE,
    OPTIONAL,
    TYPED,
    COOLDOWN,
    DEFAULT,
    RANGE,
)

__all__ = [
    # Core
    "Bot",
    "initBot",
    
    # Objects
    "Context",
    "SyncContext",
    "Embed",
    "Button",
    "Sender",
    
    # Database
    "Database",
    
    # Constants & Flag Functions
    "NOPREFIX",
    "HIDDEN",
    "REPEATABLE",
    "AUTOARGS",
    "SLASH",
    "ONCE",
    "BACKGROUND",
    "LOGGED",
    "DEL_BEFORE",
    "OPTIONAL",
    "TYPED",
    "COOLDOWN",
    "DEFAULT",
    "RANGE",
]

