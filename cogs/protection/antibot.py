import discord
from discord.ext import commands
import json
import datetime
import handlers.debug as DebugHandler
import handlers.config as config



class Antibot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_member_join(self, member):
        serverconfig = config.loadserverconfig()
        serverconfig[str(member.guild.id)] = serverconfig.get(str(member.guild.id), {})

        if not serverconfig[str(member.guild.id)].get("protection"):
            DebugHandler.LogDebug(f"Protection is not enabled for {member.guild.name}")  
            return

        if member.bot:
            DebugHandler.LogDebug(f"Bot detected: {member.name}")  

            try:
                audit_logs = await member.guild.audit_logs(limit=5, action=discord.AuditLogAction.bot_add).flatten()
                inviter = None
                for log in audit_logs:
                    if log.target.id == member.id:
                        inviter = log.user
                        DebugHandler.LogDebug(f"Bot {member.name} was invited by {inviter.name}")  
                        break
                if inviter is None:
                    DebugHandler.LogError(f"Could not find the inviter for bot {member.name} in {member.guild.name}")  
            except Exception as e:
                DebugHandler.LogError(f"Error while fetching audit logs: {e}")  
                raise Exception("Error while fetching audit logs" + str(e))

            if member.public_flags.verified_bot:
                DebugHandler.LogDebug(f"Verified bot detected: {member.name}")  
                if serverconfig[str(member.guild.id)].get("protectionlogchannel"):
                    try:
                        protection_log_channel = await member.guild.fetch_channel(serverconfig[str(member.guild.id)]["protectionlogchannel"])
                        print(f"Found protection log channel: {protection_log_channel.name}")  
                        reaction_embed = discord.Embed(
                            title="🤖 Bot Joined! 🎉",
                            description=f"{member.mention} has joined the server as a **verified bot** and has been allowed to stay. ✅",
                            color=discord.Color.green()
                        )
                        reaction_embed.set_footer(text=f"Invited by: {inviter.name}", icon_url=inviter.avatar.url if inviter else "")
                        reaction_embed.add_field(name="Bot Name", value=member.name)
                        reaction_embed.add_field(name="Bot ID", value=member.id)
                        reaction_embed.add_field(name="Bot Discriminator", value=member.discriminator)
                        reaction_embed.add_field(name="Bot Mention", value=member.mention)
                        reaction_embed.timestamp = datetime.datetime.utcnow()
                        reaction_embed.set_thumbnail(url=member.guild.icon.url)
                        await protection_log_channel.send(embed=reaction_embed)
                        DebugHandler.LogDebug("Message sent to protection log channel for verified bot.")  
                    except Exception as e:
                        DebugHandler.LogError(f"Error while sending message to log channel: {e}") 
                        raise Exception("Error while sending message to log channel" + str(e))
            else:
                DebugHandler.LogDebug(f"Unverified bot detected: {member.name}")  
                if serverconfig[str(member.guild.id)].get("protectionlogchannel"):
                    if serverconfig[str(member.guild.id)].get("protection"):
                        print(f"Protection is enabled, kicking unverified bot: {member.name}")  
                        try:
                            await member.kick(reason="Unverified bot 🚫")
                            DebugHandler.LogDebug(f"Kicked bot: {member.name}")  
                        except Exception as e:
                            DebugHandler.LogError(f"Error while kicking bot: {e}")  
                            protection_log_channel = await member.guild.fetch_channel(serverconfig[str(member.guild.id)]["protectionlogchannel"])
                            reaction_embed = discord.Embed(
                                title="⚠️ Unverified Bot NOT Kicked! ❌",
                                description=f"{member.mention} joined as an **unverified bot** and could not be kicked due to an error. 🛡️",
                                color=discord.Color.red()
                            )
                            raise Exception("Error while kicking bot" + str(e))

                        try:
                            protection_log_channel = await member.guild.fetch_channel(serverconfig[str(member.guild.id)]["protectionlogchannel"])
                            reaction_embed = discord.Embed(
                                title="⚠️ Unverified Bot Kicked! ❌",
                                description=f"{member.mention} joined as an **unverified bot** and has been kicked for security reasons. 🛡️",
                                color=discord.Color.red()
                            )
                            reaction_embed.set_footer(text=f"Invited by: {inviter.name}", icon_url=inviter.avatar.url if inviter else "")
                            reaction_embed.add_field(name="Bot Name", value=member.name)
                            reaction_embed.add_field(name="Bot ID", value=member.id)
                            reaction_embed.add_field(name="Bot Discriminator", value=member.discriminator)
                            reaction_embed.add_field(name="Bot Mention", value=member.mention)
                            reaction_embed.timestamp = datetime.datetime.utcnow()
                            reaction_embed.set_thumbnail(url=member.guild.icon.url)
                            await protection_log_channel.send(embed=reaction_embed)
                            DebugHandler.LogDebug("Message sent to protection log channel for unverified bot.")  
                        except Exception as e:
                            DebugHandler.LogError(f"Error while sending message to log channel: {e}")  
                            raise Exception("Error while sending message to log channel" + str(e))
                    else:
                        try:
                            protection_log_channel = await member.guild.fetch_channel(serverconfig[str(member.guild.id)]["protectionlogchannel"])
                            reaction_embed = discord.Embed(
                                title="🔴 Unverified Bot Allowed to Stay 🚷",
                                description=f"{member.mention} joined as an **unverified bot** but has been allowed to stay. 🟢",
                                color=discord.Color.green()
                            )
                            reaction_embed.set_footer(text=f"Invited by: {inviter.name}", icon_url=inviter.avatar.url if inviter else "")
                            reaction_embed.add_field(name="Bot Name", value=member.name)
                            reaction_embed.add_field(name="Bot ID", value=member.id)
                            reaction_embed.add_field(name="Bot Discriminator", value=member.discriminator)
                            reaction_embed.add_field(name="Bot Mention", value=member.mention)
                            reaction_embed.timestamp = datetime.datetime.utcnow()
                            reaction_embed.set_thumbnail(url=member.guild.icon.url)
                            await protection_log_channel.send(embed=reaction_embed)
                            DebugHandler.LogDebug("Message sent to protection log channel for unverified bot allowed to stay.")  
                        except Exception as e:
                            DebugHandler.LogError(f"Error while sending message to log channel: {e}")  
                else:
                    DebugHandler.LogDebug(f"Protection log channel not set for guild {member.guild.name}")  
        else:
            DebugHandler.LogDebug(f"Member is not a bot: {member.name}")  


def setup(bot):
    bot.add_cog(Antibot(bot))