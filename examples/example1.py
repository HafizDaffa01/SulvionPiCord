import spc
import random
import asyncio
import discord
from typing import Optional, Dict, List, Any, Union

# Initialize Bot
bot = spc.initBot(prefix="~", db_type="sqlite")
bot.initDB("fishing.db")

# --- Game Constants ---
FISH_TYPES: List[Dict[str, Any]] = [
    {"name": "Old Boot", "value": 0, "chance": 30, "emoji": "👢"},
    {"name": "Tiny Minnow", "value": 5, "chance": 40, "emoji": "🐟"},
    {"name": "Golden Carp", "value": 50, "chance": 20, "emoji": "🐠"},
    {"name": "Legendary Shark", "value": 500, "chance": 5, "emoji": "🦈"},
    {"name": "Kraken", "value": 2000, "chance": 1, "emoji": "🐙"},
]

def get_random_fish() -> Dict[str, Any]:
    """
    Randomly selects a fish based on weighted chances.
    """
    roll = random.randint(1, 100)
    if roll <= 30: return FISH_TYPES[0] # 30%
    elif roll <= 70: return FISH_TYPES[1] # 40%
    elif roll <= 90: return FISH_TYPES[2] # 20%
    elif roll <= 99: return FISH_TYPES[3] # 9%
    else: return FISH_TYPES[4] # 1%

# --- Database Setup ---
@bot.event
async def on_ready() -> None:
    """
    Sets up database tables when the bot starts.
    """
    if bot.db:
        # Create tables
        bot.db.create_table("users", {
            "user_id": "INTEGER PRIMARY KEY",
            "coins": "INTEGER DEFAULT 0",
            "fishes_caught": "INTEGER DEFAULT 0"
        })
        
        # Inventory table: user_id, fish_name, count
        bot.db.execute("CREATE TABLE IF NOT EXISTS inventory (user_id INTEGER, fish_name TEXT, count INTEGER, PRIMARY KEY (user_id, fish_name))")
    
    print("Fishing Bot Ready!")

# --- Helper Functions ---
def get_user(ctx: spc.Context) -> Dict[str, Any]:
    """
    Retrieve user statistics from the database, creating them if necessary.
    """
    if not ctx.db: return {}
    user = ctx.db.get("SELECT * FROM users WHERE user_id = ?", (ctx.sender.id,), one=True)
    if not user:
        ctx.db.execute("INSERT INTO users (user_id, coins, fishes_caught) VALUES (?, 0, 0)", (ctx.sender.id,))
        return {"user_id": ctx.sender.id, "coins": 0, "fishes_caught": 0}
    return dict(user)

def add_coins(ctx: spc.Context, amount: int, user_id: Optional[int] = None) -> None:
    """
    Add coins to a user's balance.
    """
    if not ctx.db: return
    uid = user_id if user_id else ctx.sender.id
    ctx.db.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, uid))

def remove_coins(ctx: spc.Context, amount: int) -> None:
    """
    Subtract coins from the sender's balance.
    """
    if not ctx.db: return
    ctx.db.execute("UPDATE users SET coins = coins - ? WHERE user_id = ?", (amount, ctx.sender.id))

def increment_fish(ctx: spc.Context) -> None:
    """
    Increment the total count of fish caught by a user.
    """
    if not ctx.db: return
    ctx.db.execute("UPDATE users SET fishes_caught = fishes_caught + 1 WHERE user_id = ?", (ctx.sender.id,))

def add_to_inventory(ctx: spc.Context, fish_name: str) -> None:
    """
    Add a specific fish to the user's inventory in the database.
    """
    if not ctx.db: return
    # Ensure user exists before adding (just in case)
    get_user(ctx)
    
    row = ctx.db.get("SELECT count FROM inventory WHERE user_id = ? AND fish_name = ?", (ctx.sender.id, fish_name), one=True)
    if row:
        ctx.db.execute("UPDATE inventory SET count = count + 1 WHERE user_id = ? AND fish_name = ?", (ctx.sender.id, fish_name))
    else:
        ctx.db.execute("INSERT INTO inventory (user_id, fish_name, count) VALUES (?, ?, 1)", (ctx.sender.id, fish_name))

def get_fish_value(name: str) -> int:
    """
    Get the coin value of a fish by its name.
    """
    for f in FISH_TYPES:
        if f['name'] == name: return int(f['value'])
    return 0

# --- Commands ---

@bot.onSlash("fish", description="Cast your line and try to catch some fish!")
async def fish(ctx: spc.Context) -> None:
    """
    Commence fishing! Cast your line and choose to Keep, Sell, or Thrash your catch.
    """
    
    get_user(ctx) # Ensure user exists
    caught = get_random_fish()
    
    # Create Embed
    color = "green" if caught['value'] > 0 else "red"
    if caught['name'] == "Kraken": color = "orange" 
    
    embed = spc.Embed(title="🎣 You cast your line...", color=color)
    embed.add_field(name="Caught", value=f"{caught['emoji']} **{caught['name']}**", inline=True)
    embed.add_field(name="Value", value=f"💰 {caught['value']} coins", inline=True)
    embed.set_footer(text="Choose an action below:")
    
    # 3 Action Buttons
    btn_keep = spc.Button(label="Keep", style="primary", custom_id=f"keep:{caught['name']}")
    btn_sell = spc.Button(label=f"Sell (+{caught['value']})", style="success", custom_id=f"sell_one:{caught['name']}")
    btn_trash = spc.Button(label="Throw Away", style="danger", custom_id="trash")

    await ctx.reply(embed=embed, components=[btn_keep, btn_sell, btn_trash])


@bot.onButton("keep")
async def on_keep_btn(ctx: spc.Context) -> None:
    """
    Callback for the 'Keep' button. Saves the fish to inventory.
    """
    if not ctx.custom_id: return
    try:
        _, fish_name = ctx.custom_id.split(":", 1)
        add_to_inventory(ctx, fish_name)
        increment_fish(ctx)
        
        await ctx.reply(f"✅ Kept **{fish_name}** in your inventory.", hidden=True, delete_after=3)
        try:
            await ctx.message.delete() # Delete the prompt to prevent double clicking
        except: pass
    except Exception as e:
        # Errors are handled by global error handler
        raise e

@bot.onButton("sell_one")
async def on_sell_one_btn(ctx: spc.Context) -> None:
    """
    Callback for the 'Sell' button. Instantly converts the catch to coins.
    """
    if not ctx.custom_id: return
    try:
        _, fish_name = ctx.custom_id.split(":", 1)
        val = get_fish_value(fish_name)
        
        add_coins(ctx, val)
        increment_fish(ctx)
        
        await ctx.reply(f"💰 Sold **{fish_name}** for **{val}** coins!", hidden=True, delete_after=3)
        try:
            await ctx.message.delete()
        except: pass
    except Exception as e:
        raise e

@bot.onButton("trash")
async def on_trash_btn(ctx: spc.Context) -> None:
    """
    Callback for the 'Throw Away' button.
    """
    try:
        await ctx.reply("🗑️ Threw it back into the sea.", hidden=True, delete_after=3)
        await ctx.message.delete()
    except: pass

@bot.onButton("sell_all")
async def on_sell_all_btn(ctx: spc.Context) -> None:
    """
    Callback to sell all inventory items.
    """
    await sell(ctx)

@bot.onSlash("sell", description="Sell all the fish in your inventory for coins.")
async def sell(ctx: spc.Context) -> None:
    """
    Command to sell all fish in your inventory.
    """

    if not ctx.db: return
    # Sell all items
    rows = ctx.db.get("SELECT * FROM inventory WHERE user_id = ?", (ctx.sender.id,))
    if not rows:
        await ctx.reply("You have no fish to sell!", hidden=True)
        return

    total_coins = 0
    items_sold = 0
    
    for row in rows:
        val = get_fish_value(row['fish_name'])
        total_coins += val * row['count']
        items_sold += row['count']
        
    # Clear Inventory
    ctx.db.execute("DELETE FROM inventory WHERE user_id = ?", (ctx.sender.id,))
    # Add Coins
    add_coins(ctx, total_coins)
    
    await ctx.reply(f"Sold **{items_sold}** fish for **{total_coins}** coins!")


@bot.onSlash("transfer", description="Transfer coins to another user.")
async def transfer_coins(ctx: spc.Context, user: discord.Member, amount: int) -> None:
    """
    Transfer coins to another user.
    """
    
    if not ctx.db: return
    sender_data = get_user(ctx)
    if sender_data.get('coins', 0) < amount:
        await ctx.reply(f"Not enough coins! You only have {sender_data.get('coins', 0)}.")
        return

    if amount <= 0:
        await ctx.reply("Invalid amount.")
        return

    target_member = user
            
    if target_member.id == ctx.sender.id:
        await ctx.reply("You cannot transfer to yourself.")
        return

    remove_coins(ctx, amount)
    user_sanity_check = ctx.db.get("SELECT * FROM users WHERE user_id = ?", (target_member.id,), one=True)
    if not user_sanity_check:
            ctx.db.execute("INSERT INTO users (user_id, coins, fishes_caught) VALUES (?, 0, 0)", (target_member.id,))
            
    add_coins(ctx, amount, user_id=target_member.id)
    
    await ctx.reply(f"💸 Transferred **{amount}** coins to **{target_member.name}**!")

@bot.onButton("show_profile")
async def on_show_profile(ctx: spc.Context) -> None:
    """
    Callback to show a user's detailed profile including balance and inventory.
    """
    if not ctx.db: return
    user = get_user(ctx)
    
    # Get Inventory
    inv_rows = ctx.db.get("SELECT * FROM inventory WHERE user_id = ?", (ctx.sender.id,))
    inv_text = "Empty"
    total_val = 0
    
    if inv_rows:
        inv_text = ""
        for row in inv_rows:
            val = get_fish_value(row['fish_name']) * row['count']
            total_val += val
            inv_text += f"• **{row['count']}x** {row['fish_name']} (Val: {val})\n"

    # Build Profile Embed
    embed = spc.Embed(title=f"👤 {ctx.sender.name}'s Profile", color="blue")
    
    # Set Thumbnail (Avatar)
    if ctx.sender.avatar_url:
        embed.set_thumbnail(url=ctx.sender.avatar_url)
        
    embed.add_field(name="💰 Balance", value=f"{user.get('coins', 0)} coins", inline=True)
    embed.add_field(name="🎣 Total Catches", value=f"{user.get('fishes_caught', 0)} fish", inline=True)
    embed.add_field(name="📦 Inventory", value=inv_text, inline=False)
    
    if total_val > 0:
         embed.set_footer(text=f"Inventory Worth: {total_val} coins")
    
    # Buttons
    comps: List[spc.Button] = []
    if inv_rows:
        comps.append(spc.Button(label="Sell All", style="success", custom_id="sell_all"))
    
    await ctx.reply(embed=embed, components=comps)

@bot.onSlash("profile", description="View your inventory and coin balance.")
async def profile(ctx: spc.Context) -> None:
    """
    Command to display your profile.
    """
    await on_show_profile(ctx)

@bot.onSlash("leaderboard", description="Check who the top fishers are!")
async def leaderboard(ctx: spc.Context) -> None:
    """
    Displays the top 5 wealthiest fishers.
    """
    
    if not ctx.db: return
    rows = ctx.db.get("SELECT * FROM users ORDER BY coins DESC LIMIT 5")
    if not rows:
        await ctx.send("No players yet!")
        return

    embed = spc.Embed(title="🏆 Fishing Leaderboard", color="yellow")
    rank = 1
    text = ""
    for row in rows:
        try:
            member = await bot.fetch_user(row['user_id'])
            name = member.name
        except:
            name = f"User {row['user_id']}"
            
        text += f"**#{rank}** {name}: 💰 {row['coins']}\n"
        rank += 1
        
    embed.description = text if text else "No players yet!"
    await ctx.reply(embed=embed)

# Start bot
bot.run("MASUKKAN-TOKEN-BOT-DISCORDMU")
