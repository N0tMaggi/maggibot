import discord
from discord.ext import commands
from discord.ui import Select, Button
import datetime
import handlers.config as config
from handlers.debug import LogError
from utils.components import build_container, build_view


def build_config_container(config_data, guild, requester, selected="all") -> discord.ui.Container:
    fields = []
    if selected == "all" or not config_data:
        if config_data:
            config_list = "\n".join([f"• **{k}:** `{v}`" for k, v in config_data.items()])
            fields.append(("📜 Active Settings", config_list, False))
        else:
            fields.append(("❌ No Configuration Found", "This server hasn't set up any custom settings yet!", False))
    else:
        value = config_data.get(selected, "Not Found")
        fields.append((f"**{selected}:**", f"`{value}`", False))

    return build_container(
        title="🔧 Server Configuration",
        description=f"**Current settings for {guild.name}**",
        color="stats",
        author=guild,
        fields=fields,
        footer_text=f"Requested by {requester.display_name}",
    )


class ConfigSelectRow(discord.ui.ActionRow):
    def __init__(self, config_data, guild):
        super().__init__()
        self.config_data = config_data
        self.guild = guild

        options = []
        if config_data:
            for key in config_data.keys():
                options.append(discord.SelectOption(label=key, value=key))
            options.append(discord.SelectOption(label="All Settings", value="all"))
        else:
            options.append(discord.SelectOption(label="No Settings", value="none", default=True))

        self.select_menu = Select(
            placeholder="Select a setting",
            options=options,
            min_values=1,
            max_values=1,
            disabled=not bool(config_data),
        )
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

    async def select_callback(self, interaction):
        selected = self.select_menu.values[0]
        container = build_config_container(self.config_data, self.guild, interaction.user, selected=selected)
        await interaction.response.edit_message(
            view=build_view(container, ConfigSelectRow(self.config_data, self.guild), ConfigCloseRow())
        )


class ConfigCloseRow(discord.ui.ActionRow):
    def __init__(self):
        super().__init__()
        self.close_button = Button(label="Close", style=discord.ButtonStyle.red)
        self.close_button.callback = self.close_callback
        self.add_item(self.close_button)

    async def close_callback(self, interaction):
        await interaction.message.delete()
        await interaction.response.defer()

class ConfigSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(administrator=True)
    async def settings_showconfig(self, ctx: discord.ApplicationContext):
        try:
            guild_id = str(ctx.guild.id)
            serverconfig = config.loadserverconfig()  
            config_data = serverconfig.get(guild_id, {})

            container = build_config_container(config_data, ctx.guild, ctx.author, selected="all")
            select_row = ConfigSelectRow(config_data, ctx.guild)
            close_row = ConfigCloseRow()

            await ctx.respond(view=build_view(container, select_row, close_row), ephemeral=False)

        except Exception as e:
            LogError(f"An error occurred while showing the server configuration: {e}")
            raise RuntimeError(f"An error occurred while showing the server configuration: {e}")

def setup(bot):
    bot.add_cog(ConfigSettings(bot))
