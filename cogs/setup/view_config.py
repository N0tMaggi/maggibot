import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.ui import View, Select, Button
from discord import ui
import datetime
import handlers.config as config
from handlers.debug import LogDebug, LogError, LogNetwork, LogSystem, LogModeration


class ConfigView(discord.ui.View):
    def __init__(self, config_data, guild):
        super().__init__(timeout=180)
        self.config_data = config_data
        self.guild = guild

        # Create Select options
        options = []
        if config_data:
            for key in config_data.keys():
                options.append(discord.SelectOption(label=key, value=key))
            options.append(discord.SelectOption(label="All Settings", value="all"))
        else:
            options.append(discord.SelectOption(
                label="No Settings",
                value="none",
                default=True
            ))

        # Configure Select menu
        self.select_menu = Select(
            placeholder="Select a setting",
            options=options,
            min_values=1,
            max_values=1
        )
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

        # Add Close button
        self.close_button = Button(
            label="Close",
            style=discord.ButtonStyle.red
        )
        self.close_button.callback = self.close_callback
        self.add_item(self.close_button)

    async def select_callback(self, interaction):
        selected = self.select_menu.values[0]
        embed = discord.Embed(
            title="🔧 Server Configuration",
            color=0x9B59B6,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(
            name=f"{self.guild.name} System Settings",
            icon_url=self.guild.icon.url if self.guild.icon else interaction.client.user.avatar.url
        )

        if selected == "all" or not self.config_data:
            if self.config_data:
                config_list = "\n".join([f"• **{k}:** `{v}`" for k, v in self.config_data.items()])
                embed.add_field(name="📜 Active Settings", value=config_list, inline=False)
            else:
                embed.add_field(
                    name="❌ No Configuration Found",
                    value="This server hasn't set up any custom settings yet!",
                    inline=False
                )
        else:
            value = self.config_data.get(selected, "Not Found")
            embed.add_field(
                name=f"**{selected}:**",
                value=f"`{value}`",
                inline=False
            )
        
        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.avatar.url
        )
        await interaction.response.edit_message(embed=embed, view=self)

    async def close_callback(self, interaction):
        await interaction.message.delete()
        await interaction.response.defer()

class ConfigSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(
        name="setup-showconfig",
        description="Show the current server configuration"
    )
    @commands.has_permissions(administrator=True)
    async def settings_showconfig(self, ctx: discord.ApplicationContext):
        try:
            guild_id = str(ctx.guild.id)
            serverconfig = config.loadserverconfig()  
            config_data = serverconfig.get(guild_id, {})

            initial_embed = discord.Embed(
                title="🔧 Server Configuration",
                description=f"**Current settings for {ctx.guild.name}**",
                color=0x9B59B6,
                timestamp=datetime.datetime.utcnow()
            )
            initial_embed.set_author(
                name=f"{ctx.guild.name} System Settings",
                icon_url=ctx.guild.icon.url if ctx.guild.icon else self.bot.user.avatar.url
            )

            if config_data:
                config_list = "\n".join([f"• **{k}:** `{v}`" for k, v in config_data.items()])
                initial_embed.add_field(name="📜 Active Settings", value=config_list, inline=False)
            else:
                initial_embed.add_field(
                    name="❌ No Configuration Found",
                    value="This server hasn't set up any custom settings yet!",
                    inline=False
                )

            initial_embed.set_footer(
                text=f"Requested by {ctx.author.display_name}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else self.bot.user.avatar.url
            )

            # Disable components if no config exists
            view = ConfigView(config_data, ctx.guild)
            if not config_data:
                view.select_menu.disabled = True
                view.close_button.disabled = False  # Keep close button enabled

            await ctx.respond(embed=initial_embed, view=view, ephemeral=False)

        except Exception as e:
            LogError(f"An error occurred while showing the server configuration: {e}")
            raise RuntimeError(f"An error occurred while showing the server configuration: {e}")

def setup(bot):
    bot.add_cog(ConfigSettings(bot))