# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.ui import View, Select, Button

from handlers.debug import LogDebug, LogModeration, LogError
from utils.embed_helpers import create_embed, create_error_embed, create_info_embed


class Role(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @slash_command(
        name="roles",
        description="Übersicht und Details zu den Server-Rollen anzeigen",
        guild_only=True,
        default_member_permissions=discord.Permissions(manage_roles=True)
    )
    @commands.has_permissions(manage_roles=True)
    async def roles(self, ctx: discord.ApplicationContext):
        guild = ctx.guild
        roles = guild.roles[1:]  # Skip @everyone
        total_roles = len(roles)
        roles_per_page = 25
        current_page = 0
        pages = max((total_roles // roles_per_page) + (1 if total_roles % roles_per_page else 0), 1)

        initial_embed = create_embed(
            title=f"🎭 Server-Rollen • {guild.name}",
            description=f"Seite **1/{pages}** • Insgesamt `{total_roles}` Rollen vorhanden",
            color="primary",
            thumbnail=guild.icon.url if guild.icon else None,
            bot_user=self.bot.user
        )

        class RoleView(View):
            def __init__(self, roles_list, cur_page=0):
                super().__init__(timeout=180)
                self.selected_role = None
                self.guild = guild
                self.roles_list = roles_list
                self.current_page = cur_page
                self.pages = pages
                self.roles_per_page = 25

                start = self.current_page * self.roles_per_page
                end = start + self.roles_per_page
                page_roles = self.roles_list[start:end]

                options = []
                for role in page_roles:
                    options.append(
                        discord.SelectOption(
                            label=role.name[:100],
                            value=str(role.id),
                            description=f"Mitglieder: {len(role.members)} | Pos: {role.position}"
                        )
                    )

                self.select_menu = Select(
                    placeholder="Wähle eine Rolle für Details...",
                    options=options if options else [discord.SelectOption(label="Keine Rollen", value="none")],
                    disabled=not bool(options)
                )
                self.select_menu.callback = self.select_callback
                self.add_item(self.select_menu)

                # Navigation Buttons
                if self.pages > 1:
                    prev_btn = Button(label="◀ Zurück", style=discord.ButtonStyle.secondary, disabled=(self.current_page == 0))
                    prev_btn.callback = self.prev_page
                    self.add_item(prev_btn)

                    next_btn = Button(label="Weiter ▶", style=discord.ButtonStyle.secondary, disabled=(self.current_page >= self.pages - 1))
                    next_btn.callback = self.next_page
                    self.add_item(next_btn)

                self.perm_button = Button(label="Berechtigungen anzeigen", style=discord.ButtonStyle.primary, emoji="🛡️", disabled=True)
                self.perm_button.callback = self.button_callback
                self.add_item(self.perm_button)

            async def prev_page(self, interaction: discord.Interaction):
                if self.current_page > 0:
                    self.current_page -= 1
                    await self.update_page(interaction)

            async def next_page(self, interaction: discord.Interaction):
                if self.current_page < self.pages - 1:
                    self.current_page += 1
                    await self.update_page(interaction)

            async def update_page(self, interaction: discord.Interaction):
                view = RoleView(self.roles_list, self.current_page)
                embed = create_embed(
                    title=f"🎭 Server-Rollen • {self.guild.name}",
                    description=f"Seite **{self.current_page+1}/{self.pages}** • Insgesamt `{len(self.roles_list)}` Rollen",
                    color="primary",
                    thumbnail=self.guild.icon.url if self.guild.icon else None,
                    bot_user=interaction.client.user
                )
                await interaction.response.edit_message(embed=embed, view=view)

            async def select_callback(self, interaction: discord.Interaction):
                try:
                    val = self.select_menu.values[0]
                    if val == "none":
                        return
                    role_id = int(val)
                    self.selected_role = self.guild.get_role(role_id)
                    if not self.selected_role:
                        await interaction.response.send_message("Rolle nicht mehr gefunden.", ephemeral=True)
                        return

                    fields = [
                        ("👥 Mitglieder", f"`{len(self.selected_role.members)}`", True),
                        ("📊 Hierarchie-Position", f"`{self.selected_role.position}`", True),
                        ("🆔 Rollen ID", f"`{self.selected_role.id}`", True),
                        ("Mention", self.selected_role.mention, True),
                        ("Separater Tab (Hoist)", "✅ Ja" if self.selected_role.hoist else "❌ Nein", True),
                        ("Erwähnbar", "✅ Ja" if self.selected_role.mentionable else "❌ Nein", True),
                        ("Erstellt am", discord.utils.format_dt(self.selected_role.created_at, 'F') if self.selected_role.created_at else "N/A", False)
                    ]

                    role_embed = create_embed(
                        title=f"Rollen-Details • {self.selected_role.name}",
                        color=self.selected_role.color.value if self.selected_role.color.value != 0 else "primary",
                        fields=fields,
                        bot_user=interaction.client.user
                    )

                    self.perm_button.disabled = False
                    await interaction.response.edit_message(embed=role_embed, view=self)
                except Exception as e:
                    LogError(f"Role selection error: {e}")
                    await interaction.response.send_message(f"Fehler: {e}", ephemeral=True)

            async def button_callback(self, interaction: discord.Interaction):
                if not self.selected_role:
                    await interaction.response.send_message("Bitte wähle zuerst eine Rolle aus.", ephemeral=True)
                    return

                perms = self.selected_role.permissions
                perm_list = [f"{'✅' if val else '❌'} {perm.replace('_', ' ').title()}" for perm, val in perms if val]

                perm_embed = create_info_embed(
                    f"🛡️ Berechtigungen für {self.selected_role.name}",
                    "\n".join(perm_list[:25]) if perm_list else "Keine speziellen Berechtigungen gewährt.",
                    color=self.selected_role.color.value if self.selected_role.color.value != 0 else "primary",
                    footer_text=f"Aktive Rechte: {len(perm_list)}"
                )
                await interaction.response.send_message(embed=perm_embed, ephemeral=True)

        view = RoleView(roles)
        await ctx.respond(embed=initial_embed, view=view, ephemeral=True)


def setup(bot: discord.Bot):
    bot.add_cog(Role(bot))
