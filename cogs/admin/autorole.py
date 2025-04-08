import discord
from discord.ext import commands
from discord.ext.commands import Cog
import datetime
import handlers.config as config
from handlers.debug import LogDebug, LogError

class AutoRole(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.serverconfig = config.loadserverconfig()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Auto give role."""
        try:
            guild_id = str(member.guild.id)
            if guild_id not in self.serverconfig or "autoroleid" not in self.serverconfig[guild_id]:
                return

            role_id = self.serverconfig[guild_id]["autoroleid"]
            role = member.guild.get_role(role_id)

            if member and role:
                await member.add_roles(role)
                LogDebug(f"Added autorole to {member.name} ({member.id}) in guild {guild_id}")
            else:
                if not member:
                    LogError(f"Member {member.id} no longer exists or is unavailable in guild {guild_id}")
                if not role:
                    LogError(f"Role {role_id} not found in guild {guild_id}")

        except Exception as e:
            LogError(f"Error in on_member_join autorole listener: {str(e)}")
            raise e 

def setup(bot):
    bot.add_cog(AutoRole(bot))
