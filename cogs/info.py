import discord
from discord.ext import commands

class InfoSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.owner_id = 1227911822875693120

    @commands.slash_command(
        name="info", 
        description="Get information about the bot"
    )
    async def info(self, ctx: discord.ApplicationContext):
        main_embed = discord.Embed(
            title="Bot Information",
            description="This bot was developed by AG7.",
            color=discord.Color.blue()
        )
        main_embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        main_embed.set_image(url="https://ag7-dev.de/favicon/favicon.ico")  
        main_embed.add_field(name="Bot Name", value=self.bot.user.name, inline=True)
        main_embed.add_field(name="Bot ID", value=self.bot.user.id, inline=True)
        main_embed.add_field(name="Bot Owner", value=f"<@{self.owner_id}>", inline=True)
        main_embed.set_footer(text="AG7 Dev Team", icon_url="https://ag7-dev.de/favicon/favicon.ico")  
        main_embed.timestamp = discord.utils.utcnow()

        support_embed = discord.Embed(
            title="Support Server",
            description="Join the support server for the bot here: [Support Server](https://discord.ag7-dev.de)\nIf you need help with the bot, you can ask in the support server or DM the bot owner.",
            color=discord.Color.green()
        )
        support_embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        support_embed.set_image(url="https://ag7-dev.de/favicon/favicon.ico")  
        support_embed.add_field(name="Bot Owner", value=f"<@{self.owner_id}>", inline=True)
        support_embed.set_footer(text="AG7 Dev Team", icon_url="https://ag7-dev.de/favicon/favicon.ico")  
        support_embed.timestamp = discord.utils.utcnow()

        await ctx.respond(embeds=[main_embed, support_embed])

def setup(bot: commands.Bot):
    bot.add_cog(InfoSystem(bot))