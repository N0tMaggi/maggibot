import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.ui import View, Select, Button
from discord import ui
import datetime
from handlers.debug import LogDebug, LogModeration, LogError

class Role(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="roles", description="Manage roles")
    async def roles(self, ctx: discord.ApplicationContext):
        guild = ctx.guild
        roles = guild.roles[1:]  # Skip @everyone
        total_roles = len(roles)
        roles_per_page = 25
        current_page = 0

        # Calculate pagination
        pages = (total_roles // roles_per_page) + (1 if total_roles % roles_per_page else 0)

        initial_embed = discord.Embed(
            title="Server Roles",
            description=f"Page 1/{pages}",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        if guild.icon:
            initial_embed.set_thumbnail(url=guild.icon.url)

        class RoleView(View):
            def __init__(self, roles, current_page=0):
                super().__init__(timeout=180)
                self.selected_role = None
                self.guild = guild
                self.roles = roles
                self.current_page = current_page
                self.roles_per_page = 25
                self.pages = pages

                start = current_page * roles_per_page
                end = start + roles_per_page
                page_roles = roles[start:end]

                # Create Select options
                options = []
                for role in page_roles:
                    options.append(
                        discord.SelectOption(
                            label=role.name[:100],
                            value=str(role.id),
                            description=f"Members: {len(role.members)} | Pos: {role.position}"
                        )
                    )

                # Select menu setup
                self.select_menu = Select(
                    placeholder="Choose a role",
                    min_values=1,
                    max_values=1,
                    options=options
                )
                self.select_menu.callback = self.select_callback
                self.add_item(self.select_menu)

                # Pagination buttons
                self.prev_button = Button(
                    label="Previous",
                    style=discord.ButtonStyle.secondary,
                    disabled=current_page == 0
                )
                self.prev_button.callback = self.prev_page
                self.add_item(self.prev_button)

                self.next_button = Button(
                    label="Next",
                    style=discord.ButtonStyle.secondary,
                    disabled=current_page >= self.pages -1
                )
                self.next_button.callback = self.next_page
                self.add_item(self.next_button)

                # Permissions button
                self.perm_button = Button(
                    label="View Permissions",
                    style=discord.ButtonStyle.secondary,
                    disabled=True
                )
                self.perm_button.callback = self.button_callback
                self.add_item(self.perm_button)

            async def update_buttons(self):
                self.prev_button.disabled = self.current_page == 0
                self.next_button.disabled = self.current_page >= self.pages -1
                await self.message.edit(view=self)

            async def prev_page(self, interaction):
                if self.current_page > 0:
                    self.current_page -= 1
                    await self.update_components(interaction)
                    await self.update_buttons()
                    LogDebug(f"Page changed to {self.current_page+1} by {interaction.user}")

            async def next_page(self, interaction):
                if self.current_page < self.pages -1:
                    self.current_page += 1
                    await self.update_components(interaction)
                    await self.update_buttons()
                    LogDebug(f"Page changed to {self.current_page+1} by {interaction.user}")

            async def update_components(self, interaction):
                start = self.current_page * self.roles_per_page
                end = start + self.roles_per_page
                page_roles = self.roles[start:end]

                new_options = []
                for role in page_roles:
                    new_options.append(
                        discord.SelectOption(
                            label=role.name[:100],
                            value=str(role.id),
                            description=f"Members: {len(role.members)} | Pos: {role.position}"
                        )
                    )

                # Update select menu options
                self.select_menu.options = new_options

                # Update embed
                embed = discord.Embed(
                    title="Server Roles",
                    description=f"Page {self.current_page+1}/{self.pages}",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now()
                )
                if self.guild.icon:
                    embed.set_thumbnail(url=self.guild.icon.url)
                await interaction.response.edit_message(embed=embed, view=self)

            async def select_callback(self, interaction):
                try:
                    role_id = int(self.select_menu.values[0])
                    self.selected_role = self.guild.get_role(role_id)
                    
                    if not self.selected_role:
                        await interaction.response.send_message(
                            "Role not found. Try again.",
                            ephemeral=True
                        )
                        return

                    # Build role details embed
                    role_embed = discord.Embed(
                        title=f"Role Details: {self.selected_role.name}",
                        color=self.selected_role.color or discord.Color.default()
                    )
                    role_embed.add_field(name="Members", value=str(len(self.selected_role.members)), inline=False)
                    role_embed.add_field(name="Position", value=str(self.selected_role.position), inline=False)
                    role_embed.add_field(name="Mention", value=self.selected_role.mention, inline=False)
                    role_embed.add_field(
                        name="Created At",
                        value=self.selected_role.created_at.strftime("%Y-%m-%d %H:%M:%S") 
                            if self.selected_role.created_at else "N/A",
                        inline=False
                    )
                    role_embed.add_field(
                        name="Hoist",
                        value="✅ Yes" if self.selected_role.hoist else "❌ No",
                        inline=True
                    )
                    role_embed.add_field(
                        name="Mentionable",
                        value="✅ Yes" if self.selected_role.mentionable else "❌ No",
                        inline=True
                    )
                    
                    self.perm_button.disabled = False
                    await interaction.response.edit_message(embed=role_embed, view=self)
                    LogDebug(f"Role selected: {self.selected_role.name} by {interaction.user}")

                except Exception as e:
                    await interaction.response.send_message(
                        f"Error: {str(e)}",
                        ephemeral=True
                    )
                    LogError(f"Role selection failed: {str(e)}")

            async def button_callback(self, interaction):
                if not self.selected_role:
                    await interaction.response.send_message(
                        "Select a role first",
                        ephemeral=True
                    )
                    return
                
                perms = self.selected_role.permissions
                perm_list = []
                for perm, value in perms:
                    perm_name = perm.replace("_", " ").title()
                    perm_list.append(f"{'✅' if value else '❌'} {perm_name}")
                
                perm_embed = discord.Embed(
                    title=f"Permissions for {self.selected_role.name}",
                    description="\n".join(perm_list[:25]) or "No permissions",
                    color=self.selected_role.color or discord.Color.default()
                )
                perm_embed.set_footer(text=f"Total permissions: {len([p for p in perms if p[1]])}")
                
                await interaction.response.send_message(
                    embed=perm_embed,
                    ephemeral=True
                )
                LogModeration(f"Permissions viewed for {self.selected_role.name}")

        view = RoleView(roles)
        view.message = await ctx.respond(embed=initial_embed, view=view, ephemeral=True)

def setup(bot):
    bot.add_cog(Role(bot))