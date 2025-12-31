![Image](https://github.com/HafizDaffa01/SulvionPiCord/blob/main/spc.png?raw=true)


[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![SQLite](https://img.shields.io/badge/SQLite-%2307405e.svg?logo=sqlite&logoColor=white)](#)
[![PyPI](https://img.shields.io/badge/PyPI-3775A9?logo=pypi&logoColor=fff)](https://pypi.org/project/sulvion-picord/)
[![Discord](https://img.shields.io/badge/Discord-7289DA?logo=discord&logoColor=fff)](#)

> [[Click here to see the PyPi page](https://pypi.org/project/sulvion-picord/0.1.0/)]

**SulvionPiCord (SPC)** is a simple and powerful Python wrapper for `discord.py`. It is designed to minimize boilerplates and make Discord bot development more intuitive, especially for beginners and rapid prototyping.

## ✨ Features

- **Simplified Decorators**: Register text commands, slash commands, and button callbacks with ease.
- **Integrated Database**: Built-in SQLite wrapper for easy data persistence.
- **Unified Context**: A single `Context` object that works across messages, interactions, and buttons.
- **Micro-Framework Style**: Inspired by modern web frameworks like Flask/FastAPI for bot events.
- **Hybrid Support**: Easily handle both asynchronous and synchronous command logic.
- **Premium Error Handling**: Automated, user-friendly error messages that stay out of your terminal.

## 🚀 Installation
- Easy, just type `pip install sulvion-picord`
- And import it using `from spc import *`

## 🛠️ Quick Start

Creating a bot is as simple as this:

```python
import spc

# Initialize Bot
bot = spc.initBot(prefix="!")

# Initialize optional database
bot.initDB("my_bot.db")

@bot.onRecv("ping")
async def ping(ctx):
    """A simple ping command."""
    await ctx.reply("Pong! 🏓")

@bot.onSlash("hello", description="Says hello!")
async def hello_slash(ctx):
    await ctx.reply(f"Hello {ctx.sender.name}!", hidden=True)

@bot.onButton("click_me")
async def on_button(ctx):
    await ctx.reply("System: Button Clicked!")

# Run the bot
bot.run("YOUR_BOT_TOKEN")
```

## 📦 Key Components

### 🤖 Bot
The core bot object, initialized with `spc.initBot()`. It handles command registration and event loop management.

### 📝 Context
A powerful unified object passed to your commands. It gives you easy access to:
- `ctx.sender`: The user who triggered the command.
- `ctx.reply()`: Smart replies (text, ephemeral, or interaction-based).
- `ctx.db`: Direct access to the integrated database.

### 🗄️ Database
A built-in SQLite wrapper.
```python
# Create a table
ctx.db.create_table("users", {"id": "INTEGER PRIMARY KEY", "score": "INTEGER"})

# Upsert data
ctx.db.upsert("users", {"id": ctx.sender.id, "score": 100})
```

## 📚 API Reference

### **Bot**
- `spc.initBot(prefix="~", ...)`: Initialize the SPC Bot instance.
- `bot.initDB(path: str)`: Connect/Create an integrated SQLite database.
- `bot.onRecv(name: str, *props)`: Decorator for text commands. Use `spc.NOPREFIX` in props for prefixless commands.
- `bot.onSlash(name: str, description: str)`: Decorator for slash commands.
- `bot.onButton(custom_id: str)`: Decorator for button callbacks.
- `bot.run(token: str)`: Starts the bot and connects to Discord.

### **Context (ctx)**
- `ctx.reply(msg=None, embed=None, components=None, hidden=False, delete_after=None)`: Intelligent reply (supports Slash, Buttons, and Text).
- `ctx.send(msg=None, ...)`: Sends a message to the current channel.
- `ctx.dm(msg=None, ...)`: Sends a direct message to the user who triggered the command.
- `ctx.react(emoji)`: Adds a reaction to the command message.
- `ctx.sleep(seconds: float)`: Asynchronous sleep utility.
- `ctx.time()`: Returns the current UNIX timestamp.
- `ctx.rand(min: int, max: int)`: Returns a random integer between min and max.
- `ctx.sender`: A `Sender` object containing `id`, `name`, `mention`, and `avatar_url`.

### **Database**
- `db.get(query, params=(), one=False)`: Fetch data from the database.
- `db.execute(query, params=())`: Execute a raw SQL query.
- `db.create_table(name, schema)`: Create a table using a dictionary `{col: type}` or raw string.
- `db.upsert(table, data: dict)`: Simple "Insert or Replace" operation.
- `db.update(table, where: dict, set_vals: dict)`: Update rows based on conditions.
- `db.delete(table, where: dict)`: Delete rows based on conditions.

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

## 👤 Author

**Hafiz Daffa W.**
- GitHub: [@HafizDaffa01](https://github.com/HafizDaffa01)





