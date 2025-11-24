import discord
from discord.ext import commands
import datetime
import asyncio
import os
from handlers.env import get_mac_channel, get_owner
from handlers.config import (
    mac_load_bans,
    mac_save_bans,
    mac_load_bypasses,
    mac_save_bypasses,
)
from extensions.macextension import trim_field, create_mac_embed

NOTIFY_CHANNEL_ID = int(get_mac_channel())
OWNER_ID = int(get_owner())

def is_owner():
    """Custom check to see if the user is the bot owner."""
    def predicate(ctx: discord.ApplicationContext) -> bool:
        return ctx.author.id == OWNER_ID
    return commands.check(predicate)

class MacBan(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        bans = mac_load_bans()
        ban_record = bans.get(str(member.id))
        if not ban_record:
            return

        bypasses = mac_load_bypasses()
        allowed_servers = bypasses.get(str(member.id), [])
        if member.guild.id in allowed_servers or str(member.guild.id) in allowed_servers:
            try:
                dm_embed = create_mac_embed(
                    title="ℹ️ MAC™ Bypass Active",
                    description=f"You are globally banned but allowed to join `{member.guild.name}`.",
                    color=discord.Color.green(),
                )
                dm_embed.add_field(
                    name="📄 Ban Reason",
                    value=f"```{trim_field(ban_record.get('reason', 'No reason provided'))}```",
                    inline=False,
                )
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                LogDebug(f"Could not send bypass DM to {member.id} - DMs disabled")
            except Exception as e:
                LogError(f"Failed to send bypass DM to {member.id}: {str(e)}")


            channel = self.bot.get_channel(NOTIFY_CHANNEL_ID)
            if channel:
                notify_embed = create_mac_embed(
                    title="✅ Bypass User Joined",
                    description="A globally banned user joined using a MAC™ bypass.",

                    color=discord.Color.green(),
                )
                notify_embed.add_field(name="👤 User", value=f"{member.mention} (`{member.id}`)", inline=True)
                notify_embed.add_field(name="🛡️ Server", value=f"`{member.guild.name}`", inline=True)
                notify_embed.add_field(
                    name="📄 Ban Reason",
                    value=f"```{trim_field(ban_record.get('reason', 'No reason provided'))}```",
                    inline=False,
                )
                notify_embed.set_thumbnail(url=member.display_avatar.url)
                await channel.send(embed=notify_embed)
            return

        attempted_server = member.guild.name
        try:
            dm_embed = create_mac_embed(
                title="🚫 Global Ban Notification",
                description=f"You are **globally banned** by MAC™ and cannot join `{member.guild.name}` or any other protected server.",
                color=discord.Color.dark_red()
            )
            dm_embed.add_field(name="Reason", value=f"```{trim_field(ban_record.get('reason', 'No reason provided'))}```", inline=False)
            dm_embed.add_field(name="Need Help?", value="> Contact support: [discord.ag7-dev.de](https://discord.ag7-dev.de)", inline=False)
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            LogDebug(f"Could not send ban DM to {member.id} - DMs disabled")
        except Exception as e:
            LogError(f"Failed to send ban DM to {member.id}: {str(e)}")

        try:
            await member.kick(reason="MAC™ Global Ban")
        except discord.Forbidden as e:
            LogError(f"Missing permissions to kick {member.id} from {member.guild.id}")
        except Exception as e:
            LogError(f"Failed to kick banned user {member.id}: {str(e)}")

        channel = self.bot.get_channel(NOTIFY_CHANNEL_ID)
        if channel:
            notify_embed = create_mac_embed(
                title="🚨 Security Alert: Banned User Detected",
                description=f"A globally banned user attempted to join a server.",
                color=discord.Color.red()
            )
            notify_embed.add_field(name="👤 User", value=f"{member.mention} (`{member.id}`)", inline=True)
            notify_embed.add_field(name="🛡️ Server", value=f"`{attempted_server}`", inline=True)
            notify_embed.add_field(name="📄 Ban Reason", value=f"```{trim_field(ban_record.get('reason', 'No reason provided'))}```", inline=False)
            notify_embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=notify_embed)

    @commands.slash_command(name="mac-ban", description="Globally bans a user from all protected servers.")
    @is_owner()
    async def macban(self, ctx: discord.ApplicationContext, user: discord.User, *, reason: str):
        bans = mac_load_bans()
        if str(user.id) in bans:
            embed = create_mac_embed(
                title="⚠️ Ban Exists",
                description=f"{user.mention} is already globally banned.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Current Reason", value=f"```{trim_field(bans[str(user.id)]['reason'])}```", inline=False)
            return await ctx.respond(embed=embed, ephemeral=True)

        ban_record = {
            "id": user.id,
            "name": user.name,
            "bandate": datetime.datetime.utcnow().isoformat(),
            "reason": reason,
            "serverid": ctx.guild.id,
            "servername": ctx.guild.name,
            "bannedby": f"{ctx.author.name} ({ctx.author.id})"
        }
        bans[str(user.id)] = ban_record
        mac_save_bans(bans)

        embed = create_mac_embed(
            title="✅ Global Ban Issued",
            description=f"**{user.mention}** has been added to the global ban list.",
            color=discord.Color.green()
        )
        embed.add_field(name="👤 User", value=f"`{user.name}` (`{user.id}`)", inline=True)
        embed.add_field(name="🛡️ Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="📄 Reason", value=f"```{reason}```", inline=False)
        embed.set_thumbnail(url=user.display_avatar.url)
        await ctx.respond(embed=embed)

        try:
            user_embed = create_mac_embed(
                title="🚫 You Have Been Globally Banned",
                description="Your account has been restricted from joining any server protected by MAC™.",
                color=discord.Color.dark_red()
            )
            user_embed.add_field(name="📄 Reason", value=f"```{reason}```", inline=False)
            user_embed.add_field(name="억 Appeal Information", value="> Contact support: [discord.ag7-dev.de](https://discord.ag7-dev.de)", inline=False)
            await user.send(embed=user_embed)
        except discord.Forbidden:
            LogDebug(f"Could not send ban notification to {user.id} - DMs disabled")
        except Exception as e:
            LogError(f"Failed to send ban notification to {user.id}: {str(e)}")

    @commands.slash_command(name="mac-bypass", description="Allows a globally banned user to join this server.")
    @commands.has_permissions(administrator=True)
    async def macbypass(self, ctx: discord.ApplicationContext, user: discord.User):
        bypasses = mac_load_bypasses()
        guild_id = ctx.guild.id
        user_id = str(user.id)
        servers = set(bypasses.get(user_id, []))
        if guild_id in servers or str(guild_id) in servers:
            embed = create_mac_embed(
                title="⚠️ Bypass Exists",
                description=f"{user.mention} already has a bypass for this server.",
                color=discord.Color.orange(),
            )
            return await ctx.respond(embed=embed, ephemeral=True)

        servers.add(guild_id)
        bypasses[user_id] = list(servers)
        mac_save_bypasses(bypasses)

        embed = create_mac_embed(
            title="✅ Bypass Added",
            description=f"{user.mention} may now join this server despite a global ban.",
            color=discord.Color.green(),
        )
        embed.add_field(name="🛡️ Server", value=f"`{ctx.guild.name}`", inline=False)
        await ctx.respond(embed=embed)

    @commands.slash_command(name="mac-unban", description="Removes a global ban from a user.")
    @is_owner()
    async def macunban(self, ctx: discord.ApplicationContext, user: discord.User):
        bans = mac_load_bans()
        if str(user.id) not in bans:
            embed = create_mac_embed(
                title="⚠️ Ban Not Found",
                description=f"{user.mention} is not on the global ban list.",
                color=discord.Color.orange()
            )
            return await ctx.respond(embed=embed, ephemeral=True)

        del bans[str(user.id)]
        mac_save_bans(bans)

        embed = create_mac_embed(
            title="✅ Global Ban Removed",
            description=f"**{user.mention}** has been removed from the global ban list.",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)

        try:
            user_embed = create_mac_embed(
                title="✅ Your Global Ban Has Been Removed",
                description="You are now able to join servers protected by MAC™ again.",
                color=discord.Color.green()
            )
            await user.send(embed=user_embed)
        except discord.Forbidden:
            LogDebug(f"Could not send unban notification to {user.id} - DMs disabled")
        except Exception as e:
            LogError(f"Failed to send unban notification to {user.id}: {str(e)}")

    @commands.slash_command(name="mac-lookup", description="Looks up a user's global ban record.")
    @is_owner()
    async def maclookup(self, ctx: discord.ApplicationContext, user: discord.User):
        bans = mac_load_bans()
        ban_record = bans.get(str(user.id))

        if not ban_record:
            embed = create_mac_embed(
                title="ℹ️ No Ban Record Found",
                description=f"{user.mention} is not globally banned.",
                color=discord.Color.blue()
            )
            return await ctx.respond(embed=embed, ephemeral=True)

        embed = create_mac_embed(
            title=f"Global Ban Record: {ban_record.get('name', 'Unknown User')}",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="👤 User", value=f"{user.mention} (`{user.id}`)", inline=False)
        embed.add_field(name="📅 Ban Date", value=f"<t:{int(datetime.datetime.fromisoformat(ban_record['bandate']).timestamp())}:F>", inline=True)
        embed.add_field(name="🛡️ Banned By", value=f"`{ban_record.get('bannedby', 'Unknown')}`", inline=True)
        embed.add_field(name="🌍 Origin Server", value=f"`{ban_record.get('servername', 'Unknown')}` (`{ban_record.get('serverid', 'N/A')}`)", inline=False)
        embed.add_field(name="📄 Reason", value=f"```{trim_field(ban_record.get('reason', 'No reason provided'))}```", inline=False)
        await ctx.respond(embed=embed)

    @commands.slash_command(name="mac-info", description="Displays statistics about the MAC™ global ban list.")
    @is_owner()
    async def macinfo(self, ctx: discord.ApplicationContext):
        bans = mac_load_bans()
        total_bans = len(bans)

        embed = create_mac_embed(
            title="MAC™ Global Ban System Statistics",
            description="An overview of the global ban database.",
            color=discord.Color.blue()
        )
        embed.add_field(name="📊 Total Bans", value=f"**{total_bans}** users are currently banned.", inline=False)

        if bans:
            recent_bans = sorted(bans.values(), key=lambda x: x['bandate'], reverse=True)[:5]
            ban_list = ""
            for ban in recent_bans:
                user_name = ban.get('name', 'Unknown')
                ban_list += f"• **{user_name}** (`{ban['id']}`) - <t:{int(datetime.datetime.fromisoformat(ban['bandate']).timestamp())}:R>\n"
            embed.add_field(name="📰 Recent Bans", value=ban_list, inline=False)

        await ctx.respond(embed=embed)

    @commands.slash_command(name="mac-export", description="Exports the complete global ban list as a file.")
    @is_owner()
    async def macexport(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        bans = mac_load_bans()
        if not bans:
            embed = create_mac_embed(
                title="ℹ️ No Ban Records",
                description="The global ban list is currently empty.",
                color=discord.Color.blue()
            )
            await ctx.followup.send(embed=embed)
            return

        filename = f"mac_global_banlist_{datetime.datetime.utcnow().strftime('%Y%m%d')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("ID | Name | Ban Date | Reason | Banned By | Server ID | Server Name\n")
            for ban in bans.values():
                line = f"{ban.get('id','N/A')} | {ban.get('name','N/A')} | {ban.get('bandate','N/A')} | {ban.get('reason','N/A')} | {ban.get('bannedby','N/A')} | {ban.get('serverid','N/A')} | {ban.get('servername','N/A')}\n"
                f.write(line)

        embed = create_mac_embed(
            title="📄 Global Ban List Exported",
            description=f"Successfully exported **{len(bans)}** entries to `{filename}`.",
            color=discord.Color.green(),
        )
        await ctx.followup.send(embed=embed, file=discord.File(filename))
        os.remove(filename)

    @commands.slash_command(name="mac-scanserver", description="Scans the current server for globally banned users.")
    @is_owner()
    async def macscanserver(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        global_bans = mac_load_bans()
        banned_members_on_server = []

        for member in ctx.guild.members:
            if str(member.id) in global_bans:
                banned_members_on_server.append(member)

        if not banned_members_on_server:
            embed = create_mac_embed(
                title="✅ Scan Complete: No Banned Users Found",
                description=f"No globally banned users were found on `{ctx.guild.name}`.",
                color=discord.Color.green()
            )
            return await ctx.followup.send(embed=embed)

        embed = create_mac_embed(
            title=f"🚨 Scan Result: {len(banned_members_on_server)} Banned User(s) Found",
            description=f"The following globally banned users are present on `{ctx.guild.name}`:",
            color=discord.Color.red()
        )

        for member in banned_members_on_server:
            ban_record = global_bans[str(member.id)]
            embed.add_field(
                name=f"👤 {member.name} (`{member.id}`)",
                value=f"**Reason:** {trim_field(ban_record.get('reason', 'N/A'))}\n**Banned By:** `{ban_record.get('bannedby', 'N/A')}`",
                inline=False
            )

        await ctx.followup.send(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(MacBan(bot))