from typing import Any, Tuple, Union

# SPC Constants
"""
SPC Constants Module
Defines property flags and argument modifiers for commands.
"""

# Command Properties
NOPREFIX = "NOPREFIX"
"""Enables a command to be triggered without the bot prefix (exact match or started with name)."""

HIDDEN = "HIDDEN"
"""Hides the command from help listings (future feature)."""

REPEATABLE = "REPEATABLE"
"""Flag for repeatable commands (future feature)."""

AUTOARGS = "AUTOARGS"
"""Automatically parses arguments (future feature)."""

SLASH = "SLASH"
"""Flag to register as a slash command."""

ONCE = "ONCE"
"""Command that can only be run once (future feature)."""

BACKGROUND = "BACKGROUND"
"""Flag for background tasks (future feature)."""

LOGGED = "LOGGED"
"""Enable logging for this command (future feature)."""

DEL_BEFORE = "DEL_BEFORE"
"""Deletes the trigger message before executing the command logic."""


# Argument Modifiers
OPTIONAL = "OPTIONAL"
"""Mark an argument as optional."""

TYPED = "TYPED"
"""Mark an argument as typed."""

def COOLDOWN(seconds: float) -> Tuple[str, float]:
    """
    Define a command cooldown.
    
    Args:
        seconds (float): Seconds to wait between uses.
        
    Returns:
        tuple: ('COOLDOWN', seconds)
    """
    return ("COOLDOWN", seconds)

def DEFAULT(value: Any) -> Tuple[str, Any]:
    """
    Define a default value for an argument.
    
    Args:
        value: The default value.
        
    Returns:
        tuple: ('DEFAULT', value)
    """
    return ("DEFAULT", value)

def RANGE(min_val: Union[int, float], max_val: Union[int, float]) -> Tuple[str, Union[int, float], Union[int, float]]:
    """
    Define a numerical range for an argument.
    
    Args:
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.
        
    Returns:
        tuple: ('RANGE', min_val, max_val)
    """
    return ("RANGE", min_val, max_val)
