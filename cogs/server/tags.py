import discord
from discord.ext import commands
from discord.commands import slash_command
import json
import asyncio
from handlers.config import load_tags, save_tags




class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tags = load_tags()

    @commands.slash_command(name = "tag", description = "Send tags")
    async def tag(self, ctx, tag: str, user: discord.Member = None):
        if tag in self.tags:
            content = self.tags[tag]
            if user:
                content = content.replace("{user}", user.mention)
            else:
                content = content.replace("{user}", ctx.author.mention)
            content = content.replace("{servername}", ctx.guild.name)
            await ctx.respond(content)
        else:
            embed = discord.Embed(
                title="❓ Tag Not Found",
                description=f"The tag **{tag}** does not exist. Please try again.",
                color=0xFF5733
            )
            await ctx.respond(embed=embed)

    @commands.slash_command(name= "tag-add" , description = "Add a tag")
    @commands.has_permissions(administrator =True)
    async def tag_add(self, ctx, tag: str):
        if tag in self.tags:
            embed = discord.Embed(
                title="❗ Tag Already Exists",
                description=f"The tag **{tag}** already exists.",
                color=0xFF5733
            )
            await ctx.respond(embed=embed)
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
                description="You took too long to provide the tag content. Please try again.",
                color=0xFF0000
            )
            await ctx.send(embed=embed)
            return

        self.tags[tag] = msg.content
        save_tags(self.tags)
        embed = discord.Embed(
            title="✅ Tag Added",
            description=f"The tag **{tag}** has been successfully added!",
            color=0x00FF00
        )
        await ctx.send(embed=embed)

    @commands.slash_command( name = "tag-remove" , description = "Remove a tag")
    @commands.has_permissions(administrator =True)
    async def tag_remove(self, ctx, tag: str):
        if tag not in self.tags:
            embed = discord.Embed(
                title="❓ Tag Not Found",
                description=f"The tag **{tag}** could not be found.",
                color=0xFF5733
            )
            await ctx.respond(embed=embed)
            return

        del self.tags[tag]
        save_tags(self.tags)
        embed = discord.Embed(
            title="🗑️ Tag Removed",
            description=f"The tag **{tag}** has been successfully removed.",
            color=0x00FF00
        )
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Tags(bot))
