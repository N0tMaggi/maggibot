import discord
from discord.ext import commands
import asyncio
import os


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

    @commands.slash_command(name="troll-spammove", description="Move a user through voice channels for 5 seconds")
    @commands.has_permissions(administrator=True)
    async def troll_spammove(self, ctx: discord.ApplicationContext, user: discord.Member):
        """Move a user through available voice channels for 5 seconds"""
        error_color = discord.Color.red()
        success_color = discord.Color.green()
        warning_color = discord.Color.orange()

        voice_channels = [ch for ch in ctx.guild.voice_channels if ch != user.voice.channel] if user.voice else []

        if not voice_channels:
            embed = discord.Embed(
                title="❌ Error",
                description="No voice channels available or user is not in a voice channel!",
                color=error_color
            )
            return await ctx.respond(embed=embed, ephemeral=True)

        if not user.voice:
            embed = discord.Embed(
                title="❌ Error",
                description="The user is not in a voice channel!",
                color=error_color
            )
            return await ctx.respond(embed=embed, ephemeral=True)

        start_embed = discord.Embed(
            title="⚠️ Troll started",
            description=f"{user.mention} will be moved through channels for 5 seconds!",
            color=warning_color
        )
        await ctx.respond(embed=start_embed)

        start_time = discord.utils.utcnow()

        try:
            for i in range(5):
                if (discord.utils.utcnow() - start_time).total_seconds() >= 5:
                    break

                target_channel = voice_channels[i % len(voice_channels)]

                try:
                    await user.move_to(target_channel, reason="Troll-Spammove")
                    await asyncio.sleep(1)  # 1 second pause per move
                except discord.Forbidden:
                    embed = discord.Embed(
                        title="❌ Missing Permissions",
                        description="I cannot move the user!",
                        color=error_color
                    )
                    await ctx.send(embed=embed)
                    break
                except discord.HTTPException as e:
                    embed = discord.Embed(
                        title="⚠️ Technical Error",
                        description=f"Error moving user: {str(e)}",
                        color=error_color
                    )
                    await ctx.send(embed=embed)
                    break

        finally:
            final_embed = discord.Embed(
                title="✅ Troll finished",
                description=f"{user.mention} has been successfully trolled!",
                color=success_color
            )
            await ctx.send(embed=final_embed)




def setup(bot: commands.Bot):
    bot.add_cog(TrollCommands(bot))
