import discord
from discord.ext import commands
import json
import datetime
import handlers.debug as DebugHandler
import handlers.config as config
import time

mention_count = {}



class Protection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def is_authorized(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        else:
            raise commands.CommandError(f"User {ctx.author} is not authorized to use this command")

    @commands.slash_command(name="setup-protectionlog", description="Set the protection log channel")
    @commands.check(is_authorized)
    async def setprotectionlogchannel(self, ctx, channel: discord.TextChannel):
        serverconfig = config.loadserverconfig()
        serverconfig[str(ctx.guild.id)] = serverconfig.get(str(ctx.guild.id), {})
        serverconfig[str(ctx.guild.id)]["protectionlogchannel"] = channel.id
        config.saveserverconfig(serverconfig)

        reaction_embed = discord.Embed(
            title="Protection Log Channel",
            description=f"Protection log channel has been set to {channel.mention}",
            color=discord.Color.green()
        )
        reaction_embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        reaction_embed.timestamp = datetime.datetime.utcnow()

        await ctx.respond(embed=reaction_embed)

    @commands.slash_command(name="setup-protection", description="Enable or disable the protection system")
    @commands.check(is_authorized)
    async def antiraid(self, ctx, enabled: bool):
        serverconfig = config.loadserverconfig()
        serverconfig[str(ctx.guild.id)] = serverconfig.get(str(ctx.guild.id), {})
        serverconfig[str(ctx.guild.id)]["protection"] = enabled
        config.saveserverconfig(serverconfig)

        reaction_embed = discord.Embed(
            title="🔒 Protection System",
            description=f"Maggi Protection system has been {'✅ Enabled' if enabled else '❌ Disabled'}",
            color=discord.Color.green() if enabled else discord.Color.red()
        )

        reaction_embed.add_field(name="Status", value="Enabled" if enabled else "Disabled", inline=True)
        reaction_embed.add_field(name="Requested By", value=f"{ctx.author.mention}", inline=True)
        reaction_embed.add_field(name="Server", value=ctx.guild.name, inline=True)

        reaction_embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        reaction_embed.timestamp = datetime.datetime.utcnow()

        if ctx.guild.icon:
            reaction_embed.set_thumbnail(url=ctx.guild.icon.url)

        await ctx.respond(embed=reaction_embed)

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



    # Event for detecting mass mentions
        @commands.Cog.listener()
        async def on_message(self, message):
            if message.author == self.bot.user:
                return
            if message.guild is None:
                return
            serverconfig = config.loadserverconfig()
            serverconfig[str(message.guild.id)] = serverconfig.get(str(message.guild.id), {})
            if not serverconfig[str(message.guild.id)].get("protection"):
                return
            if message.author.guild_permissions.administrator:
                return
            if message.author.bot:
                return
            if message.mentions:
                if len(message.mentions) > 10:
                    try:
                        protection_log_channel = await message.guild.fetch_channel(serverconfig[str(message.guild.id)]["protectionlogchannel"])
                        reaction_embed = discord.Embed(
                            title="🚨 Mass Mention Detected 🚨",
                            description=f"{message.author.mention} has sent a message with {len(message.mentions)} mentions. 🚷",
                            color=discord.Color.red()
                        )
                        reaction_embed.add_field(name="Message Content", value=message.content, inline=False)
                        reaction_embed.add_field(name="Message ID", value=message.id, inline=False)
                        reaction_embed.add_field(name="Channel", value=message.channel.mention, inline=False)
                        reaction_embed.timestamp = datetime.datetime.utcnow()
                        await protection_log_channel.send(embed=reaction_embed)
                    except Exception as e:
                        DebugHandler.LogError(f"Error while sending message to log channel: {e}")


    
def setup(bot):
    bot.add_cog(Protection(bot))
