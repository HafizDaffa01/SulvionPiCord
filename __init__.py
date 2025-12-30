# SulvionPiCord (SPC)
# Easy & Powerful Discord Bot Wrapper

__version__ = "0.1.0"

# Core
from .bot import initBot, Bot

# Context & Discord objects
from .objects import (
    Context,
    SyncContext,
    Embed,
    Button,
    Sender,
)

# Database
from .database import Database

# Constants / properties
from .const import (
    NOPREFIX,
    HIDDEN,
    SLASH,
    BACKGROUND,
    LOGGED,
    ONCE,
    COOLDOWN,
    REPEATABLE,
)

__all__ = [
    # core
    "initBot",
    "Bot",

    # context & objects
    "Context",
    "SyncContext",
    "Embed",
    "Button",
    "Sender",

    # database
    "Database",

    # constants
    "NOPREFIX",
    "HIDDEN",
    "SLASH",
    "BACKGROUND",
    "LOGGED",
    "ONCE",
    "COOLDOWN",
    "REPEATABLE",
]
