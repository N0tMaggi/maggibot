import discord
from discord import utils
from discord.ext import commands
from discord.commands import slash_command
import os
import asyncio
from utils.components import build_container, build_view

class SortedAction(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    def create_embed(self, title, description, color='info', fields=None):
        """Helper function to create uniform moderation containers."""
        return build_container(
            title=title,
            description=description,
            color=color,
            bot_user=self.bot.user,
            footer_text="Moderation Action | Bot",
            fields=fields or [],
        )

    @slash_command(name="sortedaction", description="Perform actions (ban/kick) on users with a specific role.")
    async def sortedaction(self, ctx: discord.ApplicationContext, 
                           role: discord.Role, 
                           export: bool, 
                           action: discord.Option(str, "Action to perform (ban/kick)", choices=["ban", "kick"], default=None)):
        
        # Prüfung: Hat der Nutzer die Berechtigung?
        if action == "ban" and not ctx.author.guild_permissions.ban_members:
            embed = self.create_embed("🚫 Permission Denied", "You do not have the `ban_members` permission.", color='error')
            await ctx.respond(view=build_view(embed))
            return
        elif action == "kick" and not ctx.author.guild_permissions.kick_members:
            embed = self.create_embed("🚫 Permission Denied", "You do not have the `kick_members` permission.", color='error')
            await ctx.respond(view=build_view(embed))
            return

        role_obj = discord.utils.get(ctx.guild.roles, name=role.name)
        if not role_obj:
            embed = self.create_embed("❌ Error", f"Role '{role}' not found.", color='error')
            await ctx.respond(view=build_view(embed))
            return

        members_with_role = [member for member in ctx.guild.members if role_obj in member.roles]
        total_users = len(members_with_role)

        if not total_users:
            embed = self.create_embed("🔍 No Users Found", f"No users found with the role '{role}'.", color='error')
            await ctx.respond(view=build_view(embed))
            return
        
        # Export-Bereich
        if export:
            with open("exported_users.txt", "w", encoding="utf-8") as f:
                for member in members_with_role:
                    join_date = member.joined_at.strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{member.id} | {str(member)} | Joined: {join_date}\n")
            
            embed = self.create_embed(
                "📤 Export Successful", 
                f"User IDs and join dates have been exported. **{total_users} user(s)** found.", 
                color='success',
                fields=[
                    ("📄 File Details", "Format: `ID | Username | Joined`\nFile will be deleted after sending.", False)
                ]
            )
            await ctx.respond(view=build_view(embed), file=discord.File("exported_users.txt"))
            os.remove("exported_users.txt")  # Datei löschen

        if action is None:
            embed = self.create_embed("ℹ️ No Action Performed", "Only export was requested. No ban/kick action was executed.", color='warning')
            await ctx.respond(view=build_view(embed))
            return

        # Prüfung: Hat der Bot die Berechtigung?
        if action == "ban" and not ctx.guild.me.guild_permissions.ban_members:
            embed = self.create_embed("⚠️ Permission Missing", "I do not have the `ban_members` permission.", color='error')
            await ctx.respond(view=build_view(embed))
            return
        elif action == "kick" and not ctx.guild.me.guild_permissions.kick_members:
            embed = self.create_embed("⚠️ Permission Missing", "I do not have the `kick_members` permission.", color='error')
            await ctx.respond(view=build_view(embed))
            return

        # Initialer Progress-Container
        progress_embed = self.create_embed(
            "🔄 Action Started", 
            f"Starting `{action}` for {total_users} users.", 
            color='warning',
            fields=[
                ("📊 Progress", "**Processed: 0/0**\n**Success: 0 | Failed: 0**", False)
            ]
        )
        await ctx.respond(view=build_view(progress_embed))
        progress_message = await ctx.interaction.original_response()

        # Aktion durchführen
        success_count = 0
        failed_count = 0
        for idx, member in enumerate(members_with_role, 1):
            try:
                # Selbstschutz
                if member.id == ctx.guild.me.id:
                    raise Exception("Bot cannot act on itself")
                # Serverinhaber-Schutz
                if member.id == ctx.guild.owner_id:
                    raise Exception("Cannot act on server owner")
                # Rollen-Rangfolge
                if member.top_role >= ctx.guild.me.top_role:
                    raise Exception("Member has higher or equal role")

                if action == "ban":
                    await member.ban(reason=f"Performed by {ctx.author} via /sortedaction", delete_message_days=7)
                elif action == "kick":
                    await member.kick(reason=f"Performed by {ctx.author} via /sortedaction")
                success_count += 1

            except Exception as e:
                failed_count += 1

            # Aktualisiere Progress-Container
            progress_embed = self.create_embed(
                "🔄 Action Started",
                f"Starting `{action}` for {total_users} users.",
                color='warning',
                fields=[
                    ("📊 Progress", f"**Processed: {idx}/{total_users}**\n**Success: {success_count} | Failed: {failed_count}**", False)
                ]
            )
            await progress_message.edit(view=build_view(progress_embed))
            await asyncio.sleep(0.5)  # Rate Limit Schutz 

        # Abschlussmeldung
        final_embed = self.create_embed(
            "✅ Action Completed", 
            f"Successfully {action}ed **{success_count}/{total_users}** users.", 
            color='success',
            fields=[
                ("📈 Summary", f"Success: {success_count}\nFailed: {failed_count}", False)
            ]
        )
        await progress_message.edit(view=build_view(final_embed))

def setup(bot: discord.Bot):
    bot.add_cog(SortedAction(bot))
