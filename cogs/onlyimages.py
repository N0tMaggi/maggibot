import discord
from discord.ext import commands
import json
import os

ONLY_IMAGES_FILE = "data/onlyimages.json"

def load_onlyimages():
    if not os.path.exists(ONLY_IMAGES_FILE):
        return []
    with open(ONLY_IMAGES_FILE, "r") as f:
        try:
            data = json.load(f)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

def save_onlyimages(channels):
    with open(ONLY_IMAGES_FILE, "w") as f:
        json.dump(channels, f, indent=4)

class OnlyImages(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(description="Enable only images mode in this channel.")
    @commands.has_permissions(administrator=True)
    async def enableonlyimages(self, ctx: discord.ApplicationContext):
        channels = load_onlyimages()
        channel_id = str(ctx.channel.id)
        if channel_id in channels:
            embed = discord.Embed(
                title="Already Enabled",
                description="🚫 Only images mode is already enabled in this channel.",
                color=discord.Color.orange()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        channels.append(channel_id)
        save_onlyimages(channels)
        embed = discord.Embed(
            title="Only Images Mode Enabled",
            description=f"✅ Only images mode has been enabled in <#{ctx.channel.id}>. Only messages with attachments will be allowed.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)

    @commands.slash_command(description="Disable only images mode in this channel.")
    @commands.has_permissions(administrator=True)
    async def disableonlyimages(self, ctx: discord.ApplicationContext):
        channels = load_onlyimages()
        channel_id = str(ctx.channel.id)
        if channel_id not in channels:
            embed = discord.Embed(
                title="Already Disabled",
                description="ℹ️ Only images mode is not enabled in this channel.",
                color=discord.Color.orange()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        channels.remove(channel_id)
        save_onlyimages(channels)
        embed = discord.Embed(
            title="Only Images Mode Disabled",
            description=f"✅ Only images mode has been disabled in <#{ctx.channel.id}>.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore messages from bots.
        if message.author.bot:
            return
        
        channels = load_onlyimages()
        # If the current channel is not enabled for "only images" mode, do nothing.
        if str(message.channel.id) not in channels:
            return

        # If message has no attachments, delete it and warn the user.
        if not message.attachments:
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            warning_embed = discord.Embed(
                title="Only Attachments Allowed!",
                description=f"{message.author.mention}, this channel only accepts messages with attachments (e.g. images, files).",
                color=discord.Color.red()
            )
            try:
                await message.channel.send(embed=warning_embed, delete_after=3)
            except discord.Forbidden:
                pass

def setup(bot: commands.Bot):
    bot.add_cog(OnlyImages(bot))
