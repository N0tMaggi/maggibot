import discord
from discord.ext import commands
from handlers.config import loadserverconfig 
from handlers.debug import LogDebug, LogError
from utils.components import build_container, build_view


class AntiGhostPing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = loadserverconfig() 

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild:
            return

        if not self.config.get(str(message.guild.id), {}).get("protection", False):
            return

        if not message.mentions:
            return

        LogDebug(f"Ghost ping detected in {message.guild.name} (ID: {message.guild.id})")

        fields = [
            ("Guild ID", f"`{message.guild.id}`", True),
            ("Channel ID", f"`{message.channel.id}`", True),
            ("Message ID", f"`{message.id}`", True),
        ]
        container = build_container(
            title="⚠️ Ghost Ping Alert",
            description=(
                f"You were mentioned in a message that was quickly deleted in **{message.guild.name}**\n\n"
                f"**Author:** {message.author} (`{message.author.id}`)\n"
                f"**Channel:** {message.channel.mention}\n"
                f"**Message Content:** {message.content or '*No text content*'}"
            ),
            color='error',
            thumbnail=message.author.display_avatar.url,
            fields=fields,
            timestamp=True,
        )

        for user in message.mentions:
            try:
                await user.send(view=build_view(container))
                LogDebug(f"Successfully alerted {user} (ID: {user.id})")
            except discord.Forbidden:
                LogError(f"Could not send DM to {user} (ID: {user.id}) - DMs disabled")
            except Exception as e:
                LogError(f"Error alerting {user} (ID: {user.id}): {str(e)}")

def setup(bot):
    bot.add_cog(AntiGhostPing(bot))
