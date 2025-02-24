import discord
from discord.ext import commands
import json
import datetime
import handlers.debug as debug

SERVERCONFIGFILE = "data/serverconfig.json"





# load serverconfig with error handling and corruption checks
def load_serverconfig():
    try:
        with open(SERVERCONFIGFILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        with open(SERVERCONFIGFILE, "w") as f:
            json.dump({}, f)
            return {}
    except json.JSONDecodeError:
        return {}

# save serverconfig with error handling
def save_serverconfig(serverconfig):
    with open(SERVERCONFIGFILE, "w") as f:
        json.dump(serverconfig, f, indent=4)

class Protection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def is_authorized(ctx):
        # checks if user has admin perms
        return ctx.author.guild_permissions.administrator

    @commands.slash_command(name="setprotectionlogchannel", description="Set the protection log channel")
    @commands.check(is_authorized)
    async def setprotectionlogchannel(self, ctx, channel: discord.TextChannel):
        serverconfig = load_serverconfig()
        serverconfig[str(ctx.guild.id)] = serverconfig.get(str(ctx.guild.id), {})
        serverconfig[str(ctx.guild.id)]["protectionlogchannel"] = channel.id
        save_serverconfig(serverconfig)

        reaction_embed = discord.Embed(
            title="Protection Log Channel",
            description=f"Protection log channel has been set to {channel.mention}",
            color=discord.Color.green()
        )
        reaction_embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        reaction_embed.timestamp = datetime.datetime.utcnow()
        reaction_embed.set_thumbnail(url=ctx.guild.icon.url)

        await ctx.respond(embed=reaction_embed)

    @commands.slash_command(name="protection", description="Enable or disable the protection system")
    @commands.check(is_authorized)
    async def antiraid(self, ctx, enabled: bool):
        serverconfig = load_serverconfig()
        serverconfig[str(ctx.guild.id)] = serverconfig.get(str(ctx.guild.id), {})
        serverconfig[str(ctx.guild.id)]["protection"] = enabled
        save_serverconfig(serverconfig)

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
        serverconfig = load_serverconfig()
        serverconfig[str(member.guild.id)] = serverconfig.get(str(member.guild.id), {})

        if not serverconfig[str(member.guild.id)].get("protection"):
            debug.debuglog(f"Protection is not enabled for {member.guild.name}")  # Debugging-Print
            return

        # checks if member is a bot
        if member.bot:
            debug.debuglog(f"Bot detected: {member.name}")  # Debugging-Print
            if member.public_flags.verified_bot:
                debug.debuglog(f"Verified bot detected: {member.name}")  # Debugging-Print
                if serverconfig[str(member.guild.id)].get("protectionlogchannel"):
                    try:
                        protection_log_channel = await member.guild.fetch_channel(serverconfig[str(member.guild.id)]["protectionlogchannel"])
                        print(f"Found protection log channel: {protection_log_channel.name}")  # Debugging-Print
                        reaction_embed = discord.Embed(
                            title="Bot Joined",
                            description=f"{member.mention} joined the server as a verified bot he has been allowed to stay.",
                            color=discord.Color.green()
                        )
                        reaction_embed.set_footer(text=f"Requested by {member}", icon_url=member.avatar.url)
                        reaction_embed.add_field(name="Bot Name", value=member.name)
                        reaction_embed.add_field(name="Bot ID", value=member.id)
                        reaction_embed.add_field(name="Bot Discriminator", value=member.discriminator)
                        reaction_embed.add_field(name="Bot Mention", value=member.mention)
                        reaction_embed.timestamp = datetime.datetime.utcnow()
                        reaction_embed.set_thumbnail(url=member.guild.icon.url)
                        await protection_log_channel.send(embed=reaction_embed)
                        debug.debuglog("Message sent to protection log channel for verified bot.")  # Debugging-Print
                    except Exception as e:
                        debug.debuglog(f"Error while sending message to log channel: {e}")  # Fehlerausgabe
            else:
                debug.debuglog(f"Unverified bot detected: {member.name}")  # Debugging-Print
                if serverconfig[str(member.guild.id)].get("protectionlogchannel"):
                    if serverconfig[str(member.guild.id)].get("protection"):
                        print(f"Protection is enabled, kicking unverified bot: {member.name}")  # Debugging-Print
                        try:
                            await member.kick(reason="Unverified bot")
                            debug.debuglog(f"Kicked bot: {member.name}")  # Debugging-Print
                        except Exception as e:
                            debug.debuglog(f"Error while kicking bot: {e}")  # Fehlerausgabe

                        try:
                            protection_log_channel = await member.guild.fetch_channel(serverconfig[str(member.guild.id)]["protectionlogchannel"])
                            reaction_embed = discord.Embed(
                                title="Bot Joined",
                                description=f"{member.mention} joined the server as an unverified bot and has been kicked. for security reasons.",
                                color=discord.Color.red()
                            )
                            reaction_embed.set_footer(text=f"Requested by {member}", icon_url=member.avatar.url)
                            reaction_embed.add_field(name="Bot Name", value=member.name)
                            reaction_embed.add_field(name="Bot ID", value=member.id)
                            reaction_embed.add_field(name="Bot Discriminator", value=member.discriminator)
                            reaction_embed.add_field(name="Bot Mention", value=member.mention)
                            reaction_embed.timestamp = datetime.datetime.utcnow()
                            reaction_embed.set_thumbnail(url=member.guild.icon.url)
                            await protection_log_channel.send(embed=reaction_embed)
                            debug.debuglog("Message sent to protection log channel for unverified bot.")  # Debugging-Print
                        except Exception as e:
                            debug.debuglog(f"Error while sending message to log channel: {e}")  # Fehlerausgabe
                    else:
                        try:
                            protection_log_channel = await member.guild.fetch_channel(serverconfig[str(member.guild.id)]["protectionlogchannel"])
                            reaction_embed = discord.Embed(
                                title="Bot Joined",
                                description=f"{member.mention} joined the server as an unverified bot and has been allowed to stay.",
                                color=discord.Color.green()
                            )
                            reaction_embed.set_footer(text=f"Requested by {member}", icon_url=member.avatar.url)
                            reaction_embed.add_field(name="Bot Name", value=member.name)
                            reaction_embed.add_field(name="Bot ID", value=member.id)
                            reaction_embed.add_field(name="Bot Discriminator", value=member.discriminator)
                            reaction_embed.add_field(name="Bot Mention", value=member.mention)
                            reaction_embed.timestamp = datetime.datetime.utcnow()
                            reaction_embed.set_thumbnail(url=member.guild.icon.url)
                            await protection_log_channel.send(embed=reaction_embed)
                            debug.debuglog("Message sent to protection log channel for unverified bot allowed to stay.")  # Debugging-Print
                        except Exception as e:
                            debug.debuglog(f"Error while sending message to log channel: {e}")  # Fehlerausgabe
                else:
                    debug.debuglog(f"Protection log channel not set for guild {member.guild.name}")  # Debugging-Print
        else:
            debug.debuglog(f"Member is not a bot: {member.name}")  # Debugging-Print
            

def setup(bot):
    bot.add_cog(Protection(bot))
