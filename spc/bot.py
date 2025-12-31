import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import functools
import inspect
import traceback
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Coroutine
from .objects import Context, SyncContext, Embed, Button
from .database import Database
from .const import *

T = TypeVar('T')
P = TypeVar('P')

class Bot(commands.Bot):
    """
    The main Bot class for SulvionPiCord (SPC).
    Extends discord.ext.commands.Bot with simplified decorators and integrated database support.
    """
    def __init__(self, command_prefix: str, help_command: Optional[commands.HelpCommand] = None, intents: Optional[discord.Intents] = None, **kwargs: Any) -> None:
        """
        Initialize the SPC Bot.

        Args:
            command_prefix (str): The prefix used to invoke text commands.
            help_command: Optional help command implementation.
            intents: discord.Intents to use. Defaults to default() + message_content=True.
            **kwargs: Additional arguments passed to commands.Bot.
        """
        if intents is None:
            intents = discord.Intents.default()
            intents.message_content = True
        super().__init__(command_prefix, help_command=help_command, intents=intents, **kwargs)
        self.spc_db: Optional[Database] = None
        self.db: Optional[Database] = None
        self.no_prefix_commands: Dict[str, Callable[..., Any]] = {} # name -> func
        self.button_callbacks: Dict[str, Callable[..., Any]] = {} # custom_id -> func
        self.add_listener(self._spc_on_ready, 'on_ready')
        self.tree.on_error = self._spc_on_tree_error

    async def _spc_on_tree_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        """Internal handler for slash command errors."""
        await self.on_command_error(interaction, error)

    async def _spc_on_ready(self) -> None:
        """Internal listener for bot ready event."""
        print(f"Bot @{self.user} is ONLINE!")

    async def setup_hook(self) -> None:
        """Internal hook for setting up the bot, including syncing slash commands."""
        print("Syncing slash commands globally...")
        try:
            # Sync globally (this can take up to an hour to appear, 
            # though it's usually instant for small bots)
            synced = await self.tree.sync()
            print(f"✅ Successfully synced {len(synced)} slash commands.")
            
            print("\nRegistered Commands:")
            for cmd in self.commands:
                prefix_label = f"({self.command_prefix}) "
                if cmd.name in self.no_prefix_commands:
                    prefix_label = "(no_prefix) "
                print(f" - {prefix_label}{cmd.name}")
            
            for cmd_app in synced:
                print(f" - /{cmd_app.name}")
            print("--------------------------------------\n")
            
        except Exception as e:
            print(f"❌ Failed to sync slash commands: {e}")

    def initDB(self, path: str) -> None:
        """
        Initialize the integrated database.

        Args:
            path (str): File path for the SQLite database.
        """
        self.spc_db = Database(path)
        self.db = self.spc_db
        
    async def on_message(self, message: discord.Message) -> None:
        """
        Global on_message handler. Handles NOPREFIX commands and command processing.

        Args:
            message (discord.Message): The received message.
        """
        if message.author.bot: return
        
        # Priority to NOPREFIX commands
        content = message.content
        for name, func in self.no_prefix_commands.items():
            if content == name or content.startswith(name + " "):
                ctx = Context(self, message, self.spc_db)
                args = content[len(name):].strip().split()
                try:
                    if asyncio.iscoroutinefunction(func):
                        await func(ctx, *args)
                    else:
                        sync_ctx = SyncContext(ctx)
                        await asyncio.to_thread(func, sync_ctx, *args)
                except Exception as e:
                    # Errors here are usually handled by the command logic itself or caught by global error handler if wrapped differently.
                    # For NOPREFIX we explicitly trigger the error handler if something goes wrong.
                    await self.on_command_error(message, e)  # type: ignore # Handle message as ctx in our error handler
                return

        await self.process_commands(message)

    async def on_interaction(self, interaction: discord.Interaction) -> None:
        """
        Global interaction handler. Processes button callbacks registered via @bot.onButton.

        Args:
            interaction (discord.Interaction): The interaction received.
        """
        if interaction.type == discord.InteractionType.component:
            data = interaction.data
            if not data: return
            
            custom_id = data.get("custom_id")
            if not custom_id or not isinstance(custom_id, str): return

            # Special case for the dismiss button
            if custom_id == "spc_dismiss":
                try:
                    if interaction.message:
                        await interaction.message.delete()
                except:
                    pass
                return
            
            func = None
            
            # Exact match
            if custom_id in self.button_callbacks:
                func = self.button_callbacks[custom_id]
            else:
                # Partial match (e.g. "sell:Shark" matches "sell")
                for key, cb in self.button_callbacks.items():
                    if custom_id.startswith(key + ":"):
                        func = cb
                        break
            
            if func:
                ctx = Context(self, interaction, self.spc_db)
                try:
                    if asyncio.iscoroutinefunction(func):
                        ctx.custom_id = custom_id
                        await func(ctx)
                    else:
                        ctx.custom_id = custom_id
                        sync_ctx = SyncContext(ctx)
                        sync_ctx.custom_id = custom_id
                        await asyncio.to_thread(func, sync_ctx)
                except Exception as e:
                    # Don't print to terminal, send as ephemeral message
                    await self.on_command_error(interaction, e) # type: ignore
                
                # Try to respond if not already
                if not interaction.response.is_done():
                    try:
                        await interaction.response.defer()
                    except: pass
                return
        pass

    def onRecv(self, name: str, *args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Decorator to register a text command.

        Args:
            name (str): The name of the command.
            *args: SPC properties like NOPREFIX or DEL_BEFORE.
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            is_no_prefix = False
            del_before = False
            if NOPREFIX in args: is_no_prefix = True
            if DEL_BEFORE in args: del_before = True
            
            @functools.wraps(func)
            async def wrapper(ctx: Union[commands.Context, Context], *cmd_args: Any, **cmd_kwargs: Any) -> Any:
                real_ctx = ctx
                if not isinstance(ctx, Context):
                    real_ctx = Context(self, ctx, self.spc_db)
                
                result = None
                if asyncio.iscoroutinefunction(func):
                    result = await func(real_ctx, *cmd_args, **cmd_kwargs)
                else:
                    sync_ctx = SyncContext(real_ctx) # type: ignore
                    result = await asyncio.to_thread(func, sync_ctx, *cmd_args, **cmd_kwargs)
                
                if del_before:
                    try:
                        await real_ctx.message.delete()
                    except:
                        pass
                
                return result
            
            self.command(name=name)(wrapper) # type: ignore
            if is_no_prefix:
                self.no_prefix_commands[name] = func
            return func
        return decorator

    def onSlash(self, name: str, description: str = "No description provided") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Decorator to register a slash command (with a prefix backup).
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            # Use original onRecv to provide prefix backup (~command)
            self.onRecv(name)(func)

            async def wrapper(interaction: discord.Interaction, **kwargs: Any) -> None:
                spc_ctx = Context(self, interaction, self.spc_db)
                if asyncio.iscoroutinefunction(func):
                    await func(spc_ctx, **kwargs)
                else:
                    sync_ctx = SyncContext(spc_ctx)
                    await asyncio.to_thread(func, sync_ctx, **kwargs)
            
            # Dynamic signature for Slash Options
            try:
                sig = inspect.signature(func)
                params = list(sig.parameters.values())
                if params:
                    new_params = [params[0].replace(name='interaction', annotation=discord.Interaction)] + params[1:]
                    wrapper.__signature__ = sig.replace(parameters=new_params) # type: ignore
            except: pass

            self.tree.command(name=name, description=description)(wrapper)
            return func
        return decorator

    def onButton(self, custom_id: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Decorator to register a button callback.

        Args:
            custom_id (str): The custom ID of the button.
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.button_callbacks[custom_id] = func
            return func
        return decorator

    def run(self, token: str, *, reconnect: bool = True, **kwargs: Any) -> None:
        """
        Start the bot.

        Args:
            token (str): Discord Bot Token.
            reconnect (bool): Whether to reconnect on disconnect.
        """
        try:
            super().run(token, reconnect=reconnect, **kwargs)
        except discord.errors.PrivilegedIntentsRequired:
            print("\n[SPC ERROR] Privileged Intents are missing!")
            print("Please enable 'Message Content Intent', 'Server Members Intent', and 'Presence Intent' in the Discord Developer Portal.")
            print("Reset your token if necessary. visit: https://discord.com/developers/applications\n")
        except discord.errors.LoginFailure:
            print("\n[SPC ERROR] Invalid Token!")
            print("Please check your API token.\n")

    async def on_command_error(self, ctx: Union[commands.Context, discord.Interaction, discord.Message], error: Any) -> None:
        """
        Global error handler. Silences terminal errors and provides in-chat feedback.

        Args:
            ctx: The context where the error occurred.
            error: The error object.
        """
        spc_ctx = Context(self, ctx, self.spc_db)
        
        # Unwrap InvokeErrors
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
        if isinstance(error, app_commands.AppCommandInvokeError):
            error = error.original

        # Detailed Error Handlers
        if isinstance(error, commands.MissingRequiredArgument):
            msg = f"❌ **Missing Argument:** `{error.param.name}` is required for this command."
        elif isinstance(error, commands.BadArgument):
            msg = f"❌ **Input Error:** {error}"
        elif isinstance(error, commands.CommandOnCooldown) or isinstance(error, app_commands.CommandOnCooldown):
            msg = f"⏳ **Cooldown:** Try again in {error.retry_after:.2f} seconds."
        elif isinstance(error, commands.NoPrivateMessage) or isinstance(error, app_commands.NoPrivateMessage):
            msg = "❌ This command cannot be used in private messages."
        elif isinstance(error, commands.NotOwner):
            msg = "❌ Only the owner can use this command."
        elif isinstance(error, (commands.CheckFailure, app_commands.CheckFailure)):
            msg = "❌ You don't have permission to use this command."
        elif isinstance(error, commands.CommandNotFound):
            msg = "❌ Command not found."
        else:
            tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            if len(tb) > 1000: tb = tb[:1000] + "..."
            msg = f"❌ **Internal Error:** {error}\n```python\n{tb}\n```"

        # Determine if this is a real interaction (Slash/Button) or just a Message
        is_real_interaction = False
        if isinstance(ctx, discord.Interaction):
            is_real_interaction = True
        elif hasattr(ctx, 'interaction') and ctx.interaction is not None:
            is_real_interaction = True
        
        # Create a beautiful Error Embed
        error_embed = Embed(title="System Error", color="red")
        error_embed.description = msg
        
        # Determine footer text based on context
        footer_text = "Only you can see this message" if is_real_interaction else "Only you can see this (click Dismiss below)"
        error_embed.set_footer(text=footer_text)

        try:
            await spc_ctx.reply(embed=error_embed, hidden=True)
        except Exception as e:
            print(f"[SPC ERROR] Failed to send error reply: {e}")
            try:
                await spc_ctx.send(f"⚠️ **Error:** {msg}")
            except:
                pass

    def validator(self, func: Callable[..., Any]) -> None:
        """Reserved for future use."""
        pass

def initBot(prefix: str = "~", allow_slash: bool = True, db_type: str = "sqlite", auto_validator: bool = True, intents: Optional[discord.Intents] = None) -> Bot:
    """
    Convenience function to initialize an SPC Bot.

    Args:
        prefix (str): Text command prefix.
        allow_slash (bool): Enable slash command syncing.
        db_type (str): Database type (default: sqlite).
        auto_validator (bool): Reserved.
        intents (discord.Intents): Custom intents.
        
    Returns:
        Bot: The initialized SPC Bot.
    """
    if intents is None:
        intents = discord.Intents.default()
        intents.message_content = True
    bot = Bot(command_prefix=prefix, intents=intents)
    return bot
