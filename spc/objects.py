import discord
import random
import asyncio
from typing import Optional, Union, List, Any, Dict, TYPE_CHECKING, Iterable
from discord.ext import commands
from discord.utils import MISSING

if TYPE_CHECKING:
    from .database import Database
    from .bot import Bot

class Embed(discord.Embed):
    """
    Simplified discord.Embed subclass with easier color mapping and method chaining.
    """
    def __init__(self, title: Optional[str] = None, description: Optional[str] = None, color: Optional[Union[int, str]] = None, **kwargs: Any) -> None:
        """
        Initialize an Embed.

        Args:
            title (str, optional): The title.
            description (str, optional): The description.
            color (Union[int, str], optional): Color as hex int or name (e.g., 'red', 'green').
            **kwargs: Standard discord.Embed properties.
        """
        # Simple color mapping
        final_color: Optional[int] = None
        if isinstance(color, str):
            c_lower = color.lower()
            if c_lower == "red": final_color = 0xFF0000
            elif c_lower == "green": final_color = 0x00FF00
            elif c_lower == "blue": final_color = 0x0000FF
            elif c_lower == "yellow": final_color = 0xFFFF00
            elif c_lower == "orange": final_color = 0xFFA500
            elif c_lower == "black": final_color = 0x000000
            elif c_lower == "white": final_color = 0xFFFFFF
            else: final_color = 0x7289DA # Default blurredple
        elif isinstance(color, int):
            final_color = color

        super().__init__(title=title, description=description, color=final_color, **kwargs)

    def set_thumbnail(self, *, url: Optional[Any]) -> 'Embed':
        """Set the thumbnail of the embed."""
        super().set_thumbnail(url=url)
        return self

    def set_image(self, *, url: Optional[Any]) -> 'Embed':
        """Set the main image of the embed."""
        super().set_image(url=url)
        return self
        
    def add_field(self, *, name: Any, value: Any, inline: bool = True) -> 'Embed':
        """Add a field to the embed."""
        super().add_field(name=name, value=value, inline=inline)
        return self
    
    def set_footer(self, *, text: Optional[Any] = MISSING, icon_url: Optional[Any] = MISSING) -> 'Embed':
        """Set the footer of the embed."""
        kwargs = {}
        if text is not MISSING: kwargs['text'] = text
        if icon_url is not MISSING: kwargs['icon_url'] = icon_url
        super().set_footer(**kwargs)
        return self

class Button(discord.ui.Button):
    """
    Simplified discord.ui.Button subclass with easier style mapping.
    """
    def __init__(self, label: str, style: str = "primary", custom_id: Optional[str] = None) -> None:
        """
        Initialize a Button.

        Args:
            label (str): The button text.
            style (str): Style name ('primary', 'secondary', 'success', 'danger', 'link').
            custom_id (str, optional): Custom ID for callback handling.
        """
        d_style = discord.ButtonStyle.primary
        if style in ["secondary", "gray"]: d_style = discord.ButtonStyle.secondary
        elif style in ["success", "green"]: d_style = discord.ButtonStyle.success
        elif style in ["danger", "red"]: d_style = discord.ButtonStyle.danger
        elif style in ["link", "url"]: d_style = discord.ButtonStyle.link
        
        super().__init__(label=label, style=d_style, custom_id=custom_id)

class Sender:
    """
    Wrapper for discord.User/Member to provide simplified access to common properties.
    """
    def __init__(self, user: Union[discord.User, discord.Member]) -> None:
        """
        Initialize a Sender.

        Args:
            user: The raw discord user object.
        """
        self._user: Union[discord.User, discord.Member] = user
        self.id: int = user.id
        self.name: str = user.name
        self.discriminator: str = user.discriminator # type: ignore
        self.bot: bool = user.bot
        
    @property
    def mention(self) -> str:
        """The user's mention string."""
        return self._user.mention
        
    @property
    def avatar_url(self) -> str:
        """The URL of the user's display avatar."""
        return self._user.display_avatar.url

    def role(self) -> Optional[str]:
        """Returns the name of the user's highest role, or None."""
        if isinstance(self._user, discord.Member) and self._user.top_role:
            return self._user.top_role.name
        return None
    
    def has_role(self, role_name: str) -> bool:
        """Checks if the user has a specific role by name."""
        if isinstance(self._user, discord.Member):
            for r in self._user.roles:
                if r.name == role_name:
                    return True
        return False

class Context:
    """
    Unified context object that wraps Message, Interaction, or View context.
    Provides simplified methods for interacting with the bot.
    """
    def __init__(self, bot: 'Bot', ctx: Union[commands.Context, discord.Message, discord.Interaction], db: Optional['Database'] = None) -> None:
        """
        Initialize SPC Context.
        """
        self.bot: 'Bot' = bot
        self._ctx: Union[commands.Context, discord.Message, discord.Interaction] = ctx
        self.db: Optional['Database'] = db
        self.custom_id: Optional[str] = None
        
        if isinstance(ctx, commands.Context):
            self.message: discord.Message = ctx.message
            self.channel: Any = ctx.channel
            self.guild: Optional[discord.Guild] = ctx.guild
            self.sender: Sender = Sender(ctx.author)
            self._real_ctx: Optional[Union[commands.Context, discord.Interaction]] = ctx
        elif isinstance(ctx, discord.Message):
            self.message = ctx
            self.channel = ctx.channel
            self.guild = ctx.guild
            self.sender = Sender(ctx.author)
            self._real_ctx = None
        elif isinstance(ctx, discord.Interaction):
            self.message = ctx.message # type: ignore
            self.channel = ctx.channel # type: ignore
            self.guild = ctx.guild
            self.sender = Sender(ctx.user)
            self._real_ctx = ctx # Treated as interaction context

    def _prepare_send_kwargs(self, msg: Optional[str], embed: Optional[discord.Embed], file: Optional[Union[str, discord.File]], components: Optional[List[Any]], hidden: bool, delete_after: Optional[float] = None) -> Dict[str, Any]:
        """Internal helper to prepare kwargs for discord API calls."""
        kwargs: Dict[str, Any] = {}
        if msg is not None: kwargs['content'] = msg
        if embed is not None: kwargs['embed'] = embed
        if delete_after is not None: kwargs['delete_after'] = delete_after
        
        f = self._process_file(file)
        if f is not None: kwargs['file'] = f
        
        view = self._create_view(components)
        if view is not None: kwargs['view'] = view
        elif components is not None and len(components) == 0:
            pass
            
        return kwargs

    async def reply(self, msg: Optional[str] = None, embed: Optional[discord.Embed] = None, file: Optional[Union[str, discord.File]] = None, components: Optional[List[Any]] = None, hidden: bool = False, delete_after: Optional[float] = None) -> Any:
        """
        Reply to the current context.

        Args:
            msg: text content.
            embed: Embed object.
            file: path to file or discord.File.
            components: list of discord.ui.Item or SPC Buttons.
            hidden: True for ephemeral messages.
            delete_after: Auto-delete delay in seconds.
        """
        if hidden and not isinstance(self._real_ctx, discord.Interaction):
            if components is None: components = []
            # Add a dismiss button if not already present
            has_dismiss = False
            for c in components:
                if hasattr(c, 'custom_id') and c.custom_id == "spc_dismiss":
                    has_dismiss = True
                    break
            if not has_dismiss:
                components.append(Button(label="Dismiss", style="secondary", custom_id="spc_dismiss"))

        kwargs = self._prepare_send_kwargs(msg, embed, file, components, hidden, delete_after)
        
        # Handle interaction context
        if isinstance(self._real_ctx, discord.Interaction):
            if hidden: kwargs['ephemeral'] = True
            if not self._real_ctx.response.is_done():
                await self._real_ctx.response.send_message(**kwargs)
            else:
                await self._real_ctx.followup.send(**kwargs)
            return

        # Handle message/command context
        # Removed default 10s auto-delete for hidden prefix commands to make it optional.
        if hidden:
             pass # Hidden doesn't naturally exist for prefix commands, so we don't force deletion.

        try:
            # Try to reply to the original message
            res = None
            if isinstance(self._real_ctx, commands.Context):
                res = await self._real_ctx.reply(**kwargs)
            else:
                res = await self.message.reply(**kwargs)
            return res
        except (discord.NotFound, discord.HTTPException):
            # Fallback to sending a plain message if the reference is gone (e.g. message deleted)
            if hasattr(self.channel, 'send'):
                return await self.channel.send(**kwargs)
            return None

    async def send(self, msg: Optional[str] = None, embed: Optional[discord.Embed] = None, file: Optional[Union[str, discord.File]] = None, components: Optional[List[Any]] = None, delete_after: Optional[float] = None) -> Any:
        """Send a message to the current channel."""
        kwargs = self._prepare_send_kwargs(msg, embed, file, components, False, delete_after)
        if hasattr(self.channel, 'send'):
            return await self.channel.send(**kwargs) # type: ignore
        return None

    async def dm(self, msg: Optional[str] = None, embed: Optional[discord.Embed] = None, file: Optional[Union[str, discord.File]] = None, components: Optional[List[Any]] = None, delete_after: Optional[float] = None) -> Any:
        """Send a direct message to the sender."""
        kwargs = self._prepare_send_kwargs(msg, embed, file, components, False, delete_after)
        try:
            return await self.sender._user.send(**kwargs)
        except Exception as e:
            print(f"[SPC ERROR] DM failed: {e}")

    async def react(self, emoji: Union[discord.Emoji, discord.PartialEmoji, str]) -> None:
        """Add a reaction to the original message."""
        await self.message.add_reaction(emoji)

    async def remove_react(self, emoji: Union[discord.Emoji, discord.PartialEmoji, str], user_id: Optional[int] = None) -> None:
        """Remove a reaction."""
        pass

    async def sleep(self, seconds: float) -> None:
        """Async sleep."""
        await asyncio.sleep(seconds)
        
    def time(self) -> float:
        """Get current unix timestamp."""
        import time
        return time.time()

    def rand(self, min_val: int, max_val: int) -> int:
        """Generate a random integer."""
        return random.randint(min_val, max_val)

    def _create_view(self, components: Optional[Iterable[discord.ui.Item]]) -> Optional[discord.ui.View]:
        """Internal helper to create a View from a list of components."""
        if not components: return None
        view = discord.ui.View()
        for item in components:
            if isinstance(item, discord.ui.Item):
                view.add_item(item)
        return view

    def _process_file(self, file_path: Optional[Union[str, discord.File]]) -> Optional[discord.File]:
        """Internal helper to convert string paths to discord.File."""
        if file_path and isinstance(file_path, str):
            return discord.File(file_path)
        return file_path # type: ignore

class SyncContext:
    """
    Thread-safe synchronous wrapper for Context.
    Allows use of async Context methods in standard synchronous functions (when run via threads).
    """
    def __init__(self, async_ctx: Context) -> None:
        """Initialize SyncContext."""
        self._ctx: Context = async_ctx
        self.bot: 'Bot' = async_ctx.bot
        self.db: Optional['Database'] = async_ctx.db
        self.message: discord.Message = async_ctx.message
        self.channel: Any = async_ctx.channel
        self.guild: Optional[discord.Guild] = async_ctx.guild
        self.sender: Sender = async_ctx.sender
        self.custom_id: Optional[str] = None

    def _run(self, coro: Any) -> Any:
        """Run a coroutine in the bot's loop and wait for the result synchronously."""
        future = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
        return future.result()

    def reply(self, *args: Any, **kwargs: Any) -> Any:
        """Sync version of reply()."""
        return self._run(self._ctx.reply(*args, **kwargs))

    def send(self, *args: Any, **kwargs: Any) -> Any:
        """Sync version of send()."""
        return self._run(self._ctx.send(*args, **kwargs))

    def dm(self, *args: Any, **kwargs: Any) -> Any:
        """Sync version of dm()."""
        return self._run(self._ctx.dm(*args, **kwargs))

    def react(self, *args: Any, **kwargs: Any) -> None:
        """Sync version of react()."""
        self._run(self._ctx.react(*args, **kwargs))

    def remove_react(self, *args: Any, **kwargs: Any) -> None:
        """Sync version of remove_react()."""
        self._run(self._ctx.remove_react(*args, **kwargs))

    def sleep(self, seconds: float) -> None:
        """Synchronous sleep (blocks calling thread)."""
        import time
        time.sleep(seconds)

    def time(self) -> float:
        """Sync counterpart to time()."""
        return self._ctx.time()
        
    def rand(self, *args: Any, **kwargs: Any) -> int:
        """Sync counterpart to rand()."""
        return self._ctx.rand(*args, **kwargs)
