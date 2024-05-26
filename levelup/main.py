import asyncio
import logging
import typing as t

import orjson
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.data_manager import bundled_data_path, cog_data_path
from redbot.core.i18n import Translator, cog_i18n
from redbot.core.utils.chat_formatting import humanize_list

from .abc import CompositeMetaClass
from .common.models import DB, run_migrations

log = logging.getLogger("red.vrt.levelup")
_ = Translator("LevelUp", __file__)
RequestType = t.Literal["discord_deleted_user", "owner", "user", "user_strict"]


@cog_i18n(_)
class LevelUp(commands.Cog, metaclass=CompositeMetaClass):
    """
    Your friendly neighborhood leveling system

    Earn experience by chatting in text and voice channels, compare levels with your friends, customize your profile and view various leaderboards!
    """

    __author__ = "[vertyco](https://github.com/vertyco/vrt-cogs)"
    __version__ = "4.0.0"
    __contributors__ = [
        "[aikaterna](https://github.com/aikaterna/aikaterna-cogs)",
        "[AAA3A](https://github.com/AAA3A-AAA3A/AAA3A-cogs)",
    ]

    def __init__(self, bot: Red, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot: Red = bot
        self.db: DB = DB()

        # Root Paths
        self.cog_path = cog_data_path(self)
        self.bundled_path = bundled_data_path(self)
        # Settings Files
        self.settings_file = self.cog_path / "LevelUp.json"
        self.old_settings_file = self.cog_path / "settings.json"
        # Custom Paths
        self.custom_fonts = self.cog_path / "fonts"
        self.custom_backgrounds = self.cog_path / "backgrounds"
        self.user_backgrounds = self.cog_path / "user_backgrounds"
        # Bundled Paths
        self.stock = self.bundled_path / "stock"
        self.fonts = self.bundled_path / "fonts"
        self.backgrounds = self.bundled_path / "backgrounds"

        # Save State
        self.saving = False

    async def cog_load(self) -> None:
        asyncio.create_task(self.initialize())

    async def cog_unload(self) -> None:
        self.save()

    async def initialize(self) -> None:
        await self.bot.wait_until_red_ready()
        if self.settings_file.exists():
            self.db = await asyncio.to_thread(DB.from_file, self.settings_file)
        elif self.old_settings_file.exists():
            raw_settings = self.old_settings_file.read_text()
            settings = orjson.loads(raw_settings)
            if settings:
                log.warning("Migrating old settings.json")
                try:
                    self.db = await asyncio.to_thread(run_migrations, settings)
                    log.warning("Migration complete!")
                    self.save()
                except Exception as e:
                    log.error("Failed to migrate old settings.json", exc_info=e)
                    return
            # Delete the old file
            self.old_settings_file.unlink()
        log.info("Config loaded")

        self.custom_fonts.mkdir(exist_ok=True)
        self.custom_backgrounds.mkdir(exist_ok=True)
        self.user_backgrounds.mkdir(exist_ok=True)

    def save(self) -> None:
        async def _save():
            if self.saving:
                return
            try:
                self.saving = True
                await asyncio.to_thread(self.db.to_file, self.settings_file)
            except Exception as e:
                log.error("Failed to save config", exc_info=e)
            finally:
                self.saving = False

        asyncio.create_task(_save())

    def format_help_for_context(self, ctx):
        helpcmd = super().format_help_for_context(ctx)
        info = (
            f"{helpcmd}\n"
            f"Cog Version: {self.__version__}\n"
            f"Author: {self.__author__}\n"
            f"Contributors: {humanize_list(self.__contributors__)}\n"
        )
        return info

    async def red_delete_data_for_user(self, *, requester: RequestType, user_id: int):
        return

    async def red_get_data_for_user(self, *, user_id: int):
        return
