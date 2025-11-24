import discord
from discord.ext import commands
import json
import os
from handlers.config import load_onlyimages, save_onlyimages
from handlers.debug import LogError
from utils.embed_helpers import create_embed as utils_create_embed




class OnlyImages(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = 0x2b2d31

    def create_embed(self, title, description, color=None):
        embed = utils_create_embed(
            title=title,
            description=description,
            color=color or self.embed_color,
            bot_user=self.bot.user
        )
        return embed

    @commands.slash_command(description="Enable only images mode in this channel")
    @commands.has_permissions(administrator=True)
    async def enableonlyimages(self, ctx: discord.ApplicationContext):
        """Enables image-only mode in the current channel"""
        channels = load_onlyimages()
        channel_id = str(ctx.channel.id)
        
        if channel_id in channels:
            embed = self.create_embed(
                title="⚠️ Already Enabled",
                description="This channel already has image-only mode enabled!",
                color=discord.Color.orange()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        channels[channel_id] = True
        save_onlyimages(channels)
        
        embed = self.create_embed(
            title="🖼️ Image-Only Mode Activated",
            description=f"**{ctx.channel.mention}** will now only allow messages with attachments\n\n"
                        f"• Non-attachment messages will be automatically deleted\n"
                        f"• Configured channels: `{len(channels)}`",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url="")
        await ctx.respond(embed=embed)

    @commands.slash_command(description="Disable only images mode in this channel")
    @commands.has_permissions(administrator=True)
    async def disableonlyimages(self, ctx: discord.ApplicationContext):
        """Disables image-only mode in the current channel"""
        channels = load_onlyimages()
        channel_id = str(ctx.channel.id)
        
        if channel_id not in channels:
            embed = self.create_embed(
                title="ℹ️ Not Enabled",
                description="Image-only mode is not active in this channel",
                color=discord.Color.orange()
            )
            return await ctx.respond(embed=embed, ephemeral=True)
        
        del channels[channel_id]
        save_onlyimages(channels)
        
        embed = self.create_embed(
            title="🖼️ Image-Only Mode Disabled",
            description=f"**{ctx.channel.mention}** has been restored to normal operation\n\n"
                        f"• Messages without attachments will no longer be deleted\n"
                        f"• Remaining configured channels: `{len(channels)}`",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url="")
        await ctx.respond(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.type != discord.MessageType.default:
            return
        
        channels = load_onlyimages()
        if str(message.channel.id) not in channels:
            return

        if not message.attachments:
            try:
                await message.delete()
            except discord.Forbidden:
                LogError(f"Missing permissions to delete message in {message.channel.id}")
            except Exception as e:
                LogError(f"Failed to delete non-image message: {str(e)}")
            
            warning_embed = self.create_embed(
                title="⚠️ Attachment Required",
                description=f"{message.author.mention}, this channel only allows messages with files or images!\n\n"
                            f"• Your message has been automatically deleted\n"
                            f"• Supported formats: Images, Videos, Files",
                color=discord.Color.red()
            )
            warning_embed.set_thumbnail(url="")
            
            try:
                await message.channel.send(embed=warning_embed, delete_after=10)
            except discord.Forbidden:
                LogError(f"Missing permissions to send warning in {message.channel.id}")
            except Exception as e:
                LogError(f"Failed to send image-only warning: {str(e)}")

def setup(bot: commands.Bot):
    bot.add_cog(OnlyImages(bot))