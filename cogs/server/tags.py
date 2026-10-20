# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.ui import Modal, InputText

from handlers.config import load_tags, save_tags
from handlers.debug import LogDebug, LogError
from handlers.locale import t
from utils.embed_helpers import create_embed, create_success_embed, create_error_embed, create_info_embed, create_warning_embed


class TagCreateModal(Modal):
    def __init__(self, tag_name: str, cog: "Tags", guild_id: int):
        super().__init__(title=t("tags.modal_title", guild_id=guild_id, tag_name=tag_name))
        self.tag_name = tag_name
        self.cog = cog
        self.guild_id = guild_id
        self.content_input = InputText(
            label=t("tags.modal_input_label", guild_id=guild_id),
            placeholder=t("tags.modal_input_placeholder", guild_id=guild_id),
            style=discord.InputTextStyle.long,
            max_length=1900,
            required=True
        )
        self.add_item(self.content_input)

    async def callback(self, interaction: discord.Interaction):
        guild_id_str = str(self.guild_id)
        if guild_id_str not in self.cog.tags:
            self.cog.tags[guild_id_str] = {}
        self.cog.tags[guild_id_str][self.tag_name] = self.content_input.value
        save_tags(self.cog.tags)

        embed = create_success_embed(
            t("tags.created_title", guild_id=self.guild_id),
            t("tags.created_desc", guild_id=self.guild_id, tag_name=self.tag_name)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        LogDebug(f"Tag {self.tag_name} created in guild {guild_id_str} by {interaction.user}")


class Tags(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.tags = load_tags()

    @slash_command(
        name="tag",
        description="Retrieve a stored server tag",
        guild_only=True
    )
    async def tag(self, ctx: discord.ApplicationContext, tag_name: str, user: discord.Member = None):
        gid = ctx.guild.id
        guild_id_str = str(gid)
        tag_lower = tag_name.lower().strip()
        guild_tags = self.tags.get(guild_id_str, {})

        matched_key = None
        for k in guild_tags:
            if k.lower() == tag_lower:
                matched_key = k
                break

        if not matched_key:
            embed = create_error_embed(
                t("tags.not_found_title", guild_id=gid),
                t("tags.not_found_desc", guild_id=gid, tag_name=tag_name)
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        content = guild_tags[matched_key]
        target_mention = user.mention if user else ctx.author.mention
        content = content.replace("{user}", target_mention).replace("{servername}", ctx.guild.name)

        await ctx.respond(content)
        LogDebug(f"Tag {matched_key} sent in {guild_id_str} by {ctx.author}")

    @slash_command(
        name="tag-add",
        description="Create a new server tag via modal",
        guild_only=True,
        default_member_permissions=discord.Permissions(manage_guild=True)
    )
    @commands.has_permissions(manage_guild=True)
    async def tag_add(self, ctx: discord.ApplicationContext, tag_name: str):
        gid = ctx.guild.id
        guild_id_str = str(gid)
        clean_name = tag_name.strip()
        if clean_name in self.tags.get(guild_id_str, {}):
            await ctx.respond(
                embed=create_warning_embed(
                    t("tags.already_exists_title", guild_id=gid),
                    t("tags.already_exists_desc", guild_id=gid, tag_name=clean_name)
                ),
                ephemeral=True
            )
            return

        modal = TagCreateModal(clean_name, self, gid)
        await ctx.send_modal(modal)

    @slash_command(
        name="tag-remove",
        description="Delete a server tag",
        guild_only=True,
        default_member_permissions=discord.Permissions(manage_guild=True)
    )
    @commands.has_permissions(manage_guild=True)
    async def tag_remove(self, ctx: discord.ApplicationContext, tag_name: str):
        gid = ctx.guild.id
        guild_id_str = str(gid)
        guild_tags = self.tags.get(guild_id_str, {})
        matched_key = None
        for k in guild_tags:
            if k.lower() == tag_name.lower().strip():
                matched_key = k
                break

        if not matched_key:
            await ctx.respond(
                embed=create_error_embed(
                    t("tags.not_found_title", guild_id=gid),
                    t("tags.not_found_desc", guild_id=gid, tag_name=tag_name)
                ),
                ephemeral=True
            )
            return

        del self.tags[guild_id_str][matched_key]
        if not self.tags[guild_id_str]:
            del self.tags[guild_id_str]
        save_tags(self.tags)

        await ctx.respond(
            embed=create_success_embed(
                t("tags.deleted_title", guild_id=gid),
                t("tags.deleted_desc", guild_id=gid, tag_name=matched_key)
            ),
            ephemeral=True
        )

    @slash_command(
        name="tag-list",
        description="List all available tags on this server",
        guild_only=True
    )
    async def tag_list(self, ctx: discord.ApplicationContext):
        gid = ctx.guild.id
        guild_id_str = str(gid)
        guild_tags = self.tags.get(guild_id_str, {})
        if not guild_tags:
            await ctx.respond(
                embed=create_info_embed(
                    t("tags.list_title", guild_id=gid, count=0),
                    t("tags.empty_list", guild_id=gid)
                ),
                ephemeral=True
            )
            return

        tag_list_str = "\n".join([f"• `{name}`" for name in sorted(guild_tags.keys())])
        embed = create_info_embed(
            t("tags.list_title", guild_id=gid, count=len(guild_tags)),
            tag_list_str,
            bot_user=self.bot.user
        )
        await ctx.respond(embed=embed, ephemeral=True)


def setup(bot: discord.Bot):
    bot.add_cog(Tags(bot))
