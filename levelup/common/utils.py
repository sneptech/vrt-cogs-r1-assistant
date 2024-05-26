import logging
import random
import sys
import typing as t
from datetime import datetime, timedelta

import discord
from redbot.core import commands
from redbot.core.i18n import Translator

_ = Translator("LevelUp", __file__)
log = logging.getLogger("red.vrt.levelup.formatter")


# Estimate how much time it would take to reach a certain level based on current algorithm
def time_to_level(
    xp_needed: int,
    xp_range: list,
    cooldown: int,
) -> int:
    xp_obtained = 0
    time_to_reach_level = 0  # Seconds
    while True:
        xp_obtained += random.randin(xp_range[0], xp_range[1] + 1)
        mod = (60, 7200) if random.random() < 0.75 else (5, 300)
        wait = cooldown + random.randint(*mod)
        time_to_reach_level += wait
        if xp_obtained >= xp_needed:
            return time_to_reach_level


def string_to_rgb(color: str) -> t.Tuple[int, int, int]:
    colors = {
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "cyan": (0, 255, 255),
        "magenta": (255, 0, 255),
        "white": (255, 255, 255),
        "black": (0, 0, 0),
        "purple": (128, 0, 128),
        "orange": (255, 165, 0),
        "pink": (255, 192, 203),
        "brown": (165, 42, 42),
        "teal": (0, 128, 128),
        "navy": (0, 0, 128),
        "gold": (255, 215, 0),
        "silver": (192, 192, 192),
        "gray": (128, 128, 128),
        "grey": (128, 128, 128),
        "maroon": (128, 0, 0),
        "olive": (128, 128, 0),
        "lime": (0, 128, 0),
        "aqua": (0, 255, 255),
        "fuchsia": (255, 0, 255),
        "indigo": (75, 0, 130),
        "violet": (238, 130, 238),
    }
    if color.isdigit():
        color = int(color)
        r = color & 255
        g = (color >> 8) & 255
        b = (color >> 16) & 255
        return r, g, b
    elif color in colors:
        return colors[color]
    color = color.strip("#")
    r = int(color[:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:], 16)
    return r, g, b


def get_bar(progress, total, perc=None, width: int = 15) -> str:
    fill = "▰"
    space = "▱"
    if perc is not None:
        ratio = perc / 100
    else:
        ratio = progress / total
    bar = fill * round(ratio * width) + space * round(width - (ratio * width))
    return f"{bar} {round(100 * ratio, 1)}%"


# Format time from total seconds and format into readable string
def humanize_delta(delta: t.Union[int, timedelta]) -> str:
    """Format time in seconds into a human readable string"""
    # Some time differences get sent as a float so just handle it the dumb way
    time_in_seconds = delta.total_seconds() if isinstance(delta, timedelta) else int(delta)
    minutes, seconds = divmod(time_in_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    years, days = divmod(days, 365)
    if not any([seconds, minutes, hours, days, years]):
        tstring = _("None")
    elif not any([minutes, hours, days, years]):
        if seconds == 1:
            tstring = str(seconds) + _(" second")
        else:
            tstring = str(seconds) + _(" seconds")
    elif not any([hours, days, years]):
        if minutes == 1:
            tstring = str(minutes) + _(" minute")
        else:
            tstring = str(minutes) + _(" minutes")
    elif hours and not days and not years:
        tstring = f"{hours}h {minutes}m"
    elif days and not years:
        tstring = f"{days}d {hours}h {minutes}m"
    else:
        tstring = f"{years}y {days}d {hours}h {minutes}m"
    return tstring


def get_twemoji(emoji: str) -> str:
    """Fetch the url of unicode emojis from Twemoji CDN"""
    emoji_unicode = []
    for char in emoji:
        char = hex(ord(char))[2:]
        emoji_unicode.append(char)
    if "200d" not in emoji_unicode:
        emoji_unicode = list(filter(lambda c: c != "fe0f", emoji_unicode))
    emoji_unicode = "-".join(emoji_unicode)
    return f"https://twemoji.maxcdn.com/v/latest/72x72/{emoji_unicode}.png"


def get_next_reset(weekday: int, hour: int):
    now = datetime.now()
    reset = now + timedelta((weekday - now.weekday()) % 7)
    return int(reset.replace(hour=hour, minute=0, second=0).timestamp())


def get_attachments(ctx: commands.Context) -> t.List[discord.Attachment]:
    """Get all attachments from context"""
    content = []
    if ctx.message.attachments:
        atchmts = [a for a in ctx.message.attachments]
        content.extend(atchmts)
    if hasattr(ctx.message, "reference"):
        try:
            atchmts = [a for a in ctx.message.reference.resolved.attachments]
            content.extend(atchmts)
        except AttributeError:
            pass
    return content


def deep_getsizeof(obj: t.Any, seen: t.Optional[set] = None) -> int:
    """Recursively finds the size of an object in memory"""
    if seen is None:
        seen = set()
    if id(obj) in seen:
        return 0
    # Mark object as seen
    seen.add(id(obj))
    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        # If the object is a dictionary, recursively add the size of keys and values
        size += sum([deep_getsizeof(k, seen) + deep_getsizeof(v, seen) for k, v in obj.items()])
    elif hasattr(obj, "__dict__"):
        # If the object has a __dict__, it's likely an object. Find size of its dictionary
        size += deep_getsizeof(obj.__dict__, seen)
    elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes, bytearray)):
        # If the object is an iterable (not a string or bytes), iterate through its items
        size += sum([deep_getsizeof(i, seen) for i in obj])
    elif hasattr(obj, "model_dump"):
        # If the object is a pydantic model, get the size of its dictionary
        size += deep_getsizeof(obj.model_dump(), seen)
    return size


def huminize_size(num: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"]:
        if abs(num) < 1024.0:
            return "{0:.1f}{1}".format(num, unit)
        num /= 1024.0
    return "{0:.1f}{1}".format(num, "YB")
