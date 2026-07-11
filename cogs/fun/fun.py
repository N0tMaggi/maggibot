import discord
from discord.ext import commands
import asyncio
import os
from discord import default_permissions
from utils.components import build_container, build_view

class TrollCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.assets_dir = "assets"
        os.makedirs(self.assets_dir, exist_ok=True)

    def create_embed(self, title, description, color, **kwargs):
        """Helper function to create consistent containers"""
        # Extract custom kwargs
        user = kwargs.pop("user", None)
        guild = kwargs.pop("guild", None)
        
        # Use centralized function
        container = build_container(
            title=title,
            description=description,
            color=color.value if hasattr(color, "value") else color,
            bot_user=self.bot.user,
            **kwargs
        )
        
        # Apply custom footer/author
        if user:
            container.add_item(discord.ui.TextDisplay(f"-# Requested by {user}"))
        if guild and guild.icon:
            container.add_item(
                discord.ui.Section(
                    discord.ui.TextDisplay(guild.name),
                    accessory=discord.ui.Thumbnail(guild.icon.url),
                )
            )
        
        return container

    @commands.slash_command(
        name="jumpscare", 
        description="Scare a user by joining their VC and playing a sound"
    )
    @commands.has_permissions(manage_channels=True)
    async def jumpscare(self, ctx: discord.ApplicationContext, 
                      user: discord.Member, 
                      name: str):
        """Perform a jumpscare on a user in their voice channel"""
        if not user.voice or not user.voice.channel:
            embed = self.create_embed(
                title="🚫 Operation Failed",
                description=f"{user.mention} is not in a voice channel",
                color=discord.Color.red(),
                user=ctx.author,
                guild=ctx.guild
            )
            return await ctx.respond(view=build_view(embed), ephemeral=True)
        
        voice_channel = user.voice.channel
        file_path = os.path.join(self.assets_dir, f"{name}.mp3")

        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file {name}.mp3 not found")
            
            vc = await voice_channel.connect(timeout=10)
            
            embed = self.create_embed(
                title="👻 Jumpscare Initiated",
                description=f"Target: {user.mention}\nChannel: {voice_channel.mention}",
                color=discord.Color.orange(),
                user=ctx.author,
                guild=ctx.guild
            )
            await ctx.respond(view=build_view(embed))

            source = discord.FFmpegPCMAudio(
                executable="ffmpeg",
                source=file_path,
                options="-vn -loglevel error"
            )
            
            def after_play(error):
                coro = vc.disconnect()
                fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                try:
                    fut.result()
                except Exception as e:
                    print(f"Disconnection error: {e}")

            vc.play(source, after=after_play)
            
            while vc.is_playing():
                await asyncio.sleep(0.5)

        except discord.ClientException as e:
            embed = self.create_embed(
                title="⚠️ Connection Error",
                description=str(e),
                color=discord.Color.red(),
                user=ctx.author,
                guild=ctx.guild
            )
            await ctx.respond(view=build_view(embed), ephemeral=True)
        except FileNotFoundError as e:
            embed = self.create_embed(
                title="🔍 Asset Not Found",
                description=f"Available sounds: {', '.join(self.get_available_sounds())}",
                color=discord.Color.orange(),
                user=ctx.author,
                guild=ctx.guild
            )
            await ctx.respond(view=build_view(embed), ephemeral=True)
        except Exception as e:
            embed = self.create_embed(
                title="💥 Unexpected Error",
                description=f"```{str(e)}```",
                color=discord.Color.red(),
                user=ctx.author,
                guild=ctx.guild
            )
            await ctx.respond(view=build_view(embed), ephemeral=True)
        finally:
            if ctx.guild.voice_client:
                await ctx.guild.voice_client.disconnect(force=True)

    def get_available_sounds(self):
        """Return list of available sound assets"""
        return [f[:-4] for f in os.listdir(self.assets_dir) if f.endswith(".mp3")]

    @commands.slash_command(
        name="troll-spammove", 
        description="Move a user through voice channels"
    )
    @commands.has_permissions(administrator=True)
    async def troll_spammove(self, ctx: discord.ApplicationContext, 
                           user: discord.Member):
        """Move a user through voice channels rapidly"""
        if not user.voice or not user.voice.channel:
            embed = self.create_embed(
                title="🚫 Invalid Target",
                description="User not in a voice channel",
                color=discord.Color.red(),
                user=ctx.author,
                guild=ctx.guild
            )
            return await ctx.respond(view=build_view(embed), ephemeral=True)

        voice_channels = [ch for ch in ctx.guild.voice_channels 
                         if ch != user.voice.channel and ch.permissions_for(ctx.me).move_members]
        
        if not voice_channels:
            embed = self.create_embed(
                title="🚫 No Channels Available",
                description="No movable voice channels found",
                color=discord.Color.red(),
                user=ctx.author,
                guild=ctx.guild
            )
            return await ctx.respond(view=build_view(embed), ephemeral=True)

        embed = self.create_embed(
            title="🌀 Channel Roulette Started",
            description=f"Moving {user.mention} for 5 seconds!",
            color=discord.Color.gold(),
            user=ctx.author,
            guild=ctx.guild
        )
        await ctx.respond(view=build_view(embed))

        start_time = discord.utils.utcnow()
        move_count = 0

        try:
            while (discord.utils.utcnow() - start_time).total_seconds() < 5:
                target = voice_channels[move_count % len(voice_channels)]
                try:
                    await user.move_to(target, reason="Troll command")
                    move_count += 1
                    await asyncio.sleep(0.75)
                except (discord.Forbidden, discord.HTTPException):
                    break
                except Exception as e:
                    print(f"Move error: {e}")
                    break

        finally:
            embed = self.create_embed(
                title="✅ Troll Complete",
                description=f"Moved {user.mention} {move_count} times!",
                color=discord.Color.green(),
                user=ctx.author,
                guild=ctx.guild
            )
            await ctx.followup.send(view=build_view(embed))

    @commands.slash_command(
        name="asset-upload", 
        description="Upload a new sound asset (Owner only)"
    )
    @commands.is_owner()
    async def asset_upload(self, ctx: discord.ApplicationContext, 
                         name: str, 
                         file: discord.Attachment):
        """Upload a new sound file to the assets directory"""
        if not file.filename.lower().endswith('.mp3'):
            embed = self.create_embed(
                title="❌ Invalid File Type",
                description="Only MP3 files are accepted",
                color=discord.Color.red(),
                user=ctx.author,
                guild=ctx.guild
            )
            return await ctx.respond(view=build_view(embed), ephemeral=True)

        if len(file.size) > 5 * 1024 * 1024:  
            embed = self.create_embed(
                title="❌ File Too Large",
                description="Max file size: 5MB",
                color=discord.Color.red(),
                user=ctx.author,
                guild=ctx.guild
            )
            return await ctx.respond(view=build_view(embed), ephemeral=True)

        target_path = os.path.join(self.assets_dir, f"{name}.mp3")
        
        try:
            await file.save(target_path)
            embed = self.create_embed(
                title="✅ Upload Successful",
                description=f"Saved as `{name}.mp3`",
                color=discord.Color.green(),
                user=ctx.author,
                guild=ctx.guild
            )
            embed.add_item(discord.ui.TextDisplay(f"**File Size**\n{file.size/1024:.1f} KB"))
            embed.add_item(discord.ui.TextDisplay(f"**Total Assets**\n{len(self.get_available_sounds())}"))
            await ctx.respond(view=build_view(embed))
        except Exception as e:
            embed = self.create_embed(
                title="💥 Upload Failed",
                description=f"Error: {str(e)}",
                color=discord.Color.red(),
                user=ctx.author,
                guild=ctx.guild
            )
            await ctx.respond(view=build_view(embed), ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(TrollCommands(bot))
