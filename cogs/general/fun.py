import discord
from discord.ext import commands
import asyncio
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
from io import BytesIO
import io
import textwrap

class TrollCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="jumpscare", 
        description="Perform a jumpscare on a user by joining their voice channel and playing a sound."
    )
    async def jumpscare(self, ctx: discord.ApplicationContext, user: discord.Member, name: str):
        if not user.voice or not user.voice.channel:
            embed = discord.Embed(
                title="Voice Channel Not Found",
                description=f"❌ {user.mention} is not in any voice channel.",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        voice_channel = user.voice.channel

        try:
            vc = await voice_channel.connect()
        except Exception as e:
            embed = discord.Embed(
                title="Connection Error",
                description=f"❌ Failed to join {voice_channel.mention}: {e}",
                color=discord.Color.red()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="Jumpscare Initiated",
            description=f"😱 Preparing jumpscare for {user.mention} in {voice_channel.mention}...",
            color=discord.Color.orange()
        )
        await ctx.respond(embed=embed)

        await asyncio.sleep(1)

        file_path = os.path.join("assets", f"{name}.mp3")
        if not os.path.exists(file_path):
            embed = discord.Embed(
                title="File Not Found",
                description=f"❌ The file `{name}.mp3` was not found in the assets folder.",
                color=discord.Color.red()
            )
            await vc.disconnect()
            await ctx.followup.send(embed=embed, ephemeral=True)
            return

        try:
            source = discord.FFmpegPCMAudio(file_path)
            vc.play(source)
        except Exception as e:
            await vc.disconnect()
            raise Exception(f"Failed to play audio: {e}")


        await asyncio.sleep(1)
        await vc.disconnect()

        embed = discord.Embed(
            title="Jumpscare Complete",
            description=f"😈 Jumpscare for {user.mention} has been executed.",
            color=discord.Color.green()
        )
        await ctx.followup.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(TrollCommands(bot))
