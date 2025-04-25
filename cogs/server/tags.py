import discord
from discord.ext import commands
from discord.commands import slash_command
import json
import asyncio
from handlers.config import load_tags, save_tags
from handlers.debug import LogDebug, LogError

class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tags = load_tags() 

    @slash_command(name="tag", description="Send a server-specific tag")
    async def tag(self, ctx, tag: str, user: discord.Member = None):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.tags or tag not in self.tags[guild_id]:
            embed = discord.Embed(
                title="❓ Tag Not Found",
                description=f"The tag **{tag}** does not exist in this server.",
                color=0xFF5733
            )
            await ctx.respond(embed=embed)
            LogDebug(f"Tag not found: {tag} in guild {guild_id}")
            return
        
        content = self.tags[guild_id][tag]
        if user:
            content = content.replace("{user}", user.mention)
        else:
            content = content.replace("{user}", ctx.author.mention)
        content = content.replace("{servername}", ctx.guild.name)
        
        await ctx.respond(content)
        LogDebug(f"Tag {tag} used in guild {guild_id} by {ctx.author}")

    @slash_command(name="tag-add", description="Create a new server tag")
    @commands.has_permissions(administrator=True)
    async def tag_add(self, ctx, tag: str):
        guild_id = str(ctx.guild.id)
        
        if tag in self.tags.get(guild_id, {}):
            embed = discord.Embed(
                title="❗ Tag Already Exists",
                description=f"The tag **{tag}** already exists in this server.",
                color=0xFF5733
            )
            await ctx.respond(embed=embed)
            LogDebug(f"Duplicate tag attempt: {tag} in guild {guild_id}")
            return

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        embed = discord.Embed(
            title="📝 Provide Tag Content",
            description="Please enter the content for the tag.",
            color=0x00FF00
        )
        await ctx.respond(embed=embed)

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=60)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="⌛ Timeout",
                description="Tag creation canceled due to inactivity.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            LogDebug(f"Tag creation timeout in guild {guild_id}")
            return

        # Ensure guild exists in tags structure
        if guild_id not in self.tags:
            self.tags[guild_id] = {}
        self.tags[guild_id][tag] = msg.content

        save_tags(self.tags)
        embed = discord.Embed(
            title="✅ Tag Added",
            description=f"The tag **{tag}** has been added to this server.",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
        LogDebug(f"Tag {tag} added in guild {guild_id} by {ctx.author}")

    @slash_command(name="tag-remove", description="Delete a server tag")
    @commands.has_permissions(administrator=True)
    async def tag_remove(self, ctx, tag: str):
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.tags or tag not in self.tags[guild_id]:
            embed = discord.Embed(
                title="❓ Tag Not Found",
                description=f"The tag **{tag}** does not exist in this server.",
                color=0xFF5733
            )
            await ctx.respond(embed=embed)
            LogDebug(f"Tag removal attempt for non-existing tag {tag} in guild {guild_id}")
            return

        del self.tags[guild_id][tag]
        if not self.tags[guild_id]:  # Remove empty guild entries
            del self.tags[guild_id]

        save_tags(self.tags)
        embed = discord.Embed(
            title="🗑️ Tag Removed",
            description=f"The tag **{tag}** has been removed from this server.",
            color=0x00FF00
        )
        await ctx.respond(embed=embed)
        LogDebug(f"Tag {tag} removed from guild {guild_id} by {ctx.author}")

    @tag.error
    @tag_add.error
    @tag_remove.error
    async def error_handler(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="🔒 Access Denied",
                description="You need **Administrator** permissions to use this command.",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
            LogError(f"Permission denied for {ctx.author} in guild {ctx.guild.id}")
        else:
            LogError(f"Unexpected error in tag commands: {str(error)}")
            await ctx.respond("An unexpected error occurred. Please try again later.", ephemeral=True)

def setup(bot):
    bot.add_cog(Tags(bot))
