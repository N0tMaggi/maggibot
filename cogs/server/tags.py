# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.ui import Modal, InputText

from handlers.config import load_tags, save_tags
from handlers.debug import LogDebug, LogError
from utils.embed_helpers import create_embed, create_success_embed, create_error_embed, create_info_embed, create_warning_embed


class TagCreateModal(Modal):
    def __init__(self, tag_name: str, cog: "Tags"):
        super().__init__(title=f"Tag '{tag_name}' erstellen")
        self.tag_name = tag_name
        self.cog = cog
        self.content_input = InputText(
            label="Tag-Inhalt",
            placeholder="Schreibe den Tag-Inhalt (Variablen: {user}, {servername})...",
            style=discord.InputTextStyle.long,
            max_length=1900,
            required=True
        )
        self.add_item(self.content_input)

    async def callback(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.cog.tags:
            self.cog.tags[guild_id] = {}
        self.cog.tags[guild_id][self.tag_name] = self.content_input.value
        save_tags(self.cog.tags)

        embed = create_success_embed(
            "Tag hinzugefügt",
            f"Der Tag **{self.tag_name}** wurde erfolgreich für diesen Server gespeichert."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        LogDebug(f"Tag {self.tag_name} created in guild {guild_id} by {interaction.user}")


class Tags(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.tags = load_tags()

    @slash_command(
        name="tag",
        description="Ruft einen gespeicherten Server-Tag ab",
        guild_only=True
    )
    async def tag(self, ctx: discord.ApplicationContext, tag_name: str, user: discord.Member = None):
        guild_id = str(ctx.guild.id)
        tag_lower = tag_name.lower().strip()
        guild_tags = self.tags.get(guild_id, {})

        matched_key = None
        for k in guild_tags:
            if k.lower() == tag_lower:
                matched_key = k
                break

        if not matched_key:
            embed = create_error_embed(
                "Tag nicht gefunden",
                f"Der Tag **{tag_name}** existiert auf diesem Server nicht.\nNutze `/tag-list` für eine Übersicht."
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        content = guild_tags[matched_key]
        target_mention = user.mention if user else ctx.author.mention
        content = content.replace("{user}", target_mention).replace("{servername}", ctx.guild.name)

        await ctx.respond(content)
        LogDebug(f"Tag {matched_key} sent in {guild_id} by {ctx.author}")

    @slash_command(
        name="tag-add",
        description="Erstelle einen neuen Server-Tag via interaktivem Modal",
        guild_only=True,
        default_member_permissions=discord.Permissions(manage_guild=True)
    )
    @commands.has_permissions(manage_guild=True)
    async def tag_add(self, ctx: discord.ApplicationContext, tag_name: str):
        guild_id = str(ctx.guild.id)
        clean_name = tag_name.strip()
        if clean_name in self.tags.get(guild_id, {}):
            await ctx.respond(
                embed=create_warning_embed("Bereits vorhanden", f"Der Tag **{clean_name}** existiert bereits."),
                ephemeral=True
            )
            return

        modal = TagCreateModal(clean_name, self)
        await ctx.send_modal(modal)

    @slash_command(
        name="tag-remove",
        description="Löscht einen Server-Tag",
        guild_only=True,
        default_member_permissions=discord.Permissions(manage_guild=True)
    )
    @commands.has_permissions(manage_guild=True)
    async def tag_remove(self, ctx: discord.ApplicationContext, tag_name: str):
        guild_id = str(ctx.guild.id)
        guild_tags = self.tags.get(guild_id, {})
        matched_key = None
        for k in guild_tags:
            if k.lower() == tag_name.lower().strip():
                matched_key = k
                break

        if not matched_key:
            await ctx.respond(
                embed=create_error_embed("Nicht gefunden", f"Der Tag **{tag_name}** existiert nicht."),
                ephemeral=True
            )
            return

        del self.tags[guild_id][matched_key]
        if not self.tags[guild_id]:
            del self.tags[guild_id]
        save_tags(self.tags)

        await ctx.respond(
            embed=create_success_embed("Tag gelöscht", f"Der Tag **{matched_key}** wurde entfernt."),
            ephemeral=True
        )

    @slash_command(
        name="tag-list",
        description="Zeigt alle verfügbaren Tags dieses Servers",
        guild_only=True
    )
    async def tag_list(self, ctx: discord.ApplicationContext):
        guild_id = str(ctx.guild.id)
        guild_tags = self.tags.get(guild_id, {})
        if not guild_tags:
            await ctx.respond(
                embed=create_info_embed("Keine Tags", "Auf diesem Server wurden noch keine Tags eingerichtet."),
                ephemeral=True
            )
            return

        tag_list_str = "\n".join([f"• `{name}`" for name in sorted(guild_tags.keys())])
        embed = create_info_embed(
            f"🏷️ Server Tags ({len(guild_tags)})",
            tag_list_str,
            bot_user=self.bot.user
        )
        await ctx.respond(embed=embed, ephemeral=True)


def setup(bot: discord.Bot):
    bot.add_cog(Tags(bot))
