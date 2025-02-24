import discord
from discord.ext import commands
import random
import json
import os
import asyncio

RANDOM_MATH_FILE = "data/randommathchannel.json"
COOKIES_FILE = "data/cookies.json"

def load_json(filename, default):
    if not os.path.exists(filename):
        return default
    with open(filename, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

class RandomMath(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.math_channels = load_json(RANDOM_MATH_FILE, {})
        self.cookies = load_json(COOKIES_FILE, {})
        self.active_challenges = {}

    @commands.slash_command(description="Enable random math questions in this channel.")
    @commands.has_permissions(administrator=True)
    async def enablerandommath(self, ctx: discord.ApplicationContext, chance: float):
        if not (0.1 <= chance <= 100):
            await ctx.respond("Chance must be between 0.1 and 100.", ephemeral=True)
            return
        
        self.math_channels[str(ctx.channel.id)] = chance
        save_json(RANDOM_MATH_FILE, self.math_channels)
        
        embed = discord.Embed(
            title="Random Math Enabled",
            description=f"Math challenges will now appear randomly in this channel with a **{chance}%** chance.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/271/271220.png")
        await ctx.respond(embed=embed)

    @commands.slash_command(description="Disable random math questions in this channel.")
    @commands.has_permissions(administrator=True)
    async def disablerandommath(self, ctx: discord.ApplicationContext):
        if str(ctx.channel.id) in self.math_channels:
            del self.math_channels[str(ctx.channel.id)]
            save_json(RANDOM_MATH_FILE, self.math_channels)
            embed = discord.Embed(
                title="Random Math Disabled",
                description="Math challenges have been disabled in this channel.",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/271/271220.png")
            await ctx.respond(embed=embed)
        else:
            await ctx.respond("Math challenges are not enabled in this channel.", ephemeral=True)

    @commands.slash_command(description="Check how many cookies a user has.")
    async def cookies(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        user = user or ctx.author
        count = self.cookies.get(str(user.id), 0)
        embed = discord.Embed(
            title="Cookie Count",
            description=f"{user.mention} has **{count} 🍪 cookies**!",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/956/956575.png")
        await ctx.respond(embed=embed)

    @commands.slash_command(description="Show the cookie leaderboard.")
    async def cookielist(self, ctx: discord.ApplicationContext):
        sorted_users = sorted(self.cookies.items(), key=lambda x: x[1], reverse=True)
        leaderboard = "\n".join([f"<@{user}>: **{count} 🍪**" for user, count in sorted_users[:10]])
        embed = discord.Embed(
            title="Cookie Leaderboard",
            description=leaderboard or "No cookies yet!",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/956/956575.png")
        await ctx.respond(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or str(message.channel.id) not in self.math_channels:
            return
        
        chance = self.math_channels[str(message.channel.id)]
        if random.uniform(0, 100) > chance:
            return
        
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        operation = random.choice(["+", "-", "*", "/"])
        question = f"{num1} {operation} {num2}"
        answer = round(eval(question), 2)
        
        embed = discord.Embed(
            title="Math Challenge!",
            description=f"Solve: **{question}**\nYou have **30 seconds**!",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/992/992231.png")
        await message.channel.send(embed=embed)
        self.active_challenges[message.channel.id] = (answer, message.author.id)
        
        try:
            await self.wait_for_answer(message.channel, answer, message.author.id)
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            embed = discord.Embed(
                title="Challenge Cancelled!",
                description="The challenge was cancelled.",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2989/2989989.png")
            await message.channel.send(embed=embed)
        finally:
            del self.active_challenges[message.channel.id]

    async def wait_for_answer(self, channel, answer, user_id):
        def check(msg):
            return msg.channel.id == channel.id and msg.author.id == user_id and msg.content.strip().replace(",", ".").isdigit()
        
        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            if round(float(msg.content), 2) == answer:
                self.cookies[str(msg.author.id)] = self.cookies.get(str(msg.author.id), 0) + 1
                save_json(COOKIES_FILE, self.cookies)
                embed = discord.Embed(
                    title="Correct Answer!",
                    description=f"{msg.author.mention}, you earned a **🍪 cookie**!",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2989/2989989.png")
            else:
                embed = discord.Embed(
                    title="Wrong Answer!",
                    description=f"The correct answer was **{answer}**. Better luck next time!",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2989/2989989.png")
            await channel.send(embed=embed)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="Time's Up!",
                description=f"No answer was given. The correct answer was **{answer}**.",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2989/2989989.png")
            await channel.send(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(RandomMath(bot))