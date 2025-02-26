import discord
from discord.ext import commands
from discord.commands import slash_command
import json


tagsconfigfile = "data/tags.json"

def load_tags():
    with open(tagsconfigfile, "r") as f:
        return json.load(f)
    
def save_tags(tags):
    with open(tagsconfigfile, "w") as f:
        json.dump(tags, f, indent=4)

class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tags = load_tags()

    @commands.slash_command()
    async def tag(self, ctx, tag: str, required_roles: discord.Role = None):
        if required_roles is not None:
            if not any(role in [role.id for role in ctx.author.roles] for role in required_roles):
                embed = discord.Embed(
                    title="❌ **Access Denied**",
                    description="You don't have the required roles to view this tag.",
                    color=0xFF0000
                )
                embed.set_footer(text="Please contact an administrator.")
                await ctx.respond(embed=embed)
                return
        if tag in self.tags:
            embed = discord.Embed(
                title=f"🔑 **Tag: {tag}**",
                description=self.tags[tag],
                color=0x00FF00
            )
            embed.set_footer(text="Maggi Bot Tags™")
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(
                title="❓ **Tag Not Found**",
                description=f"The tag **{tag}** does not exist. Please try again.",
                color=0xFF5733
            )
            await ctx.respond(embed=embed)

    @commands.slash_command()
    async def addtag(self, ctx, tag: str, *, content: str, required_roles: discord.Role = None):
        if required_roles is not None:
            if not any(role in [role.id for role in ctx.author.roles] for role in required_roles):
                embed = discord.Embed(
                    title="🚫 **Access Denied**",
                    description="You don't have the required roles to add a tag.",
                    color=0xFF0000
                )
                embed.set_footer(text="Please contact an administrator.")
                await ctx.respond(embed=embed)
                return
        if tag in self.tags:
            embed = discord.Embed(
                title="❗ **Tag Already Exists**",
                description=f"The tag **{tag}** already exists.",
                color=0xFF5733
            )
            await ctx.respond(embed=embed)
            return

        self.tags[tag] = content
        save_tags(self.tags)
        embed = discord.Embed(
            title="✅ **Tag Added**",
            description=f"The tag **{tag}** has been successfully added!",
            color=0x00FF00
        )
        embed.set_footer(text="Maggi Bot Tags™")
        await ctx.respond(embed=embed)

    @commands.slash_command()
    async def removetag(self, ctx, tag: str, required_roles: discord.Role = None):
        if required_roles is not None:
            if not any(role in [role.id for role in ctx.author.roles] for role in required_roles):
                embed = discord.Embed(
                    title="🚫 **Access Denied**",
                    description="You don't have the required roles to remove a tag.",
                    color=0xFF0000
                )
                embed.set_footer(text="Please contact an administrator.")
                await ctx.respond(embed=embed)
                return
        if tag not in self.tags:
            embed = discord.Embed(
                title="❓ **Tag Not Found**",
                description=f"The tag **{tag}** could not be found.",
                color=0xFF5733
            )
            await ctx.respond(embed=embed)
            return

        del self.tags[tag]
        save_tags(self.tags)
        embed = discord.Embed(
            title="🗑️ **Tag Removed**",
            description=f"The tag **{tag}** has been successfully removed.",
            color=0x00FF00
        )
        embed.set_footer(text="The tag has been successfully removed.")
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Tags(bot))
