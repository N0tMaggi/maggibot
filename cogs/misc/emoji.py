# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import rarfile
import os
import tempfile
import shutil
from io import BytesIO
import asyncio

from handlers.locale import t
from utils.embed_helpers import create_embed, create_success_embed, create_error_embed, create_warning_embed, create_info_embed


class EmojiUpload(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    def progress_bar(self, percentage: float, length: int = 12) -> str:
        filled = '▰'
        empty = '▱'
        progress = round(percentage * length)
        return f"[{filled * progress}{empty * (length - progress)}] {round(percentage * 100)}%"

    async def process_emoji_file(self, rf, file_info, guild, ctx, temp_dir):
        try:
            file_data = rf.read(file_info)
            if len(file_data) < 100:
                return False, t("emoji.too_small", ctx=ctx)

            filename = file_info.filename.lower()
            if not (filename.endswith('.gif') or filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.jpeg')):
                return False, t("emoji.invalid_format", ctx=ctx)

            base_name = os.path.basename(filename)
            emoji_name = os.path.splitext(base_name)[0][:30]
            emoji_name = ''.join(c for c in emoji_name if c.isalnum() or c in ('_', '-')).strip()
            if not emoji_name:
                return False, t("emoji.invalid_name", ctx=ctx)

            await guild.create_custom_emoji(
                name=emoji_name,
                image=file_data,
                reason=f"Batch-Upload by {ctx.author}",
            )
            return True, t("emoji.success", ctx=ctx)
        except Exception as e:
            return False, str(e)

    @commands.slash_command(
        name="asset-emoji-upload",
        description="Batch upload emojis from a RAR archive (Admin only)",
        guild_only=True,
        default_member_permissions=discord.Permissions(manage_emojis_and_stickers=True)
    )
    @commands.has_permissions(manage_emojis_and_stickers=True)
    async def emoji_upload(self, ctx: discord.ApplicationContext, rar_file: discord.Attachment):
        await ctx.defer()

        if not rar_file.filename.lower().endswith('.rar'):
            return await ctx.respond(
                embed=create_error_embed(t("common.error", ctx=ctx), t("emoji.invalid_rar", ctx=ctx)),
                ephemeral=True
            )

        guild = ctx.guild
        max_emojis = guild.emoji_limit
        current_emojis = len(guild.emojis)
        available_slots = max_emojis - current_emojis

        if available_slots <= 0:
            return await ctx.respond(
                embed=create_warning_embed(
                    t("common.warning", ctx=ctx),
                    t("emoji.slots_full", ctx=ctx, current=current_emojis, max=max_emojis)
                ),
                ephemeral=True
            )

        try:
            data = await rar_file.read()
            with rarfile.RarFile(BytesIO(data)) as rf:
                valid_files = [f for f in rf.infolist() if not f.isdir() and f.file_size > 0]
                if not valid_files:
                    return await ctx.respond(
                        embed=create_error_embed(t("common.error", ctx=ctx), "No valid image files found inside RAR archive."),
                        ephemeral=True
                    )

                upload_count = min(len(valid_files), available_slots)
                temp_dir = tempfile.mkdtemp()
                success = 0
                skipped = 0
                errors = []

                progress_embed = create_info_embed(
                    t("emoji.processing", ctx=ctx),
                    f"{self.progress_bar(0)}\n• Slots: `{current_emojis}/{max_emojis}`\n• Queued: `{upload_count}`"
                )
                await ctx.interaction.edit_original_response(embed=progress_embed)

                for idx, file_info in enumerate(valid_files[:upload_count]):
                    try:
                        res, msg = await self.process_emoji_file(rf, file_info, guild, ctx, temp_dir)
                        if res:
                            success += 1
                        else:
                            skipped += 1
                            errors.append(f"`{file_info.filename}`: {msg}")

                        if (idx + 1) % 2 == 0 or (idx + 1) == upload_count:
                            progress = (idx + 1) / upload_count
                            embed = create_info_embed(
                                f"{t('common.status', ctx=ctx)} ({idx + 1}/{upload_count})",
                                f"{self.progress_bar(progress)}\n\n• {t('common.success', ctx=ctx)}: **{success}**\n• Skipped: **{skipped}**"
                            )
                            await ctx.interaction.edit_original_response(embed=embed)
                        await asyncio.sleep(1)
                    except Exception as loop_e:
                        skipped += 1
                        errors.append(f"`{file_info.filename}`: {loop_e}")

                shutil.rmtree(temp_dir, ignore_errors=True)

                res_embed = create_success_embed(
                    t("emoji.completed_title", ctx=ctx),
                    t("emoji.completed_desc", ctx=ctx, success_count=success, fail_count=skipped)
                )
                if errors:
                    res_embed.add_field(name=t("common.details", ctx=ctx), value="\n".join(errors[:5]), inline=False)
                await ctx.interaction.edit_original_response(embed=res_embed)

        except rarfile.BadRarFile:
            await ctx.respond(embed=create_error_embed(t("common.error", ctx=ctx), "The archive could not be read as RAR."), ephemeral=True)
        except Exception as e:
            await ctx.respond(embed=create_error_embed(t("common.error", ctx=ctx), str(e)), ephemeral=True)

    @commands.slash_command(
        name="emoji-stats",
        description="Display emoji usage and server slot statistics",
        guild_only=True
    )
    async def emoji_stats(self, ctx: discord.ApplicationContext):
        guild = ctx.guild
        max_emojis = guild.emoji_limit
        total_emojis = len(guild.emojis)
        static_emojis = sum(not e.animated for e in guild.emojis)
        animated_emojis = total_emojis - static_emojis

        progress = total_emojis / max_emojis if max_emojis > 0 else 0
        embed = create_embed(
            title=f"😄 {t('general.emojis', ctx=ctx)} • {guild.name}",
            color="success" if progress < 0.8 else ("warning" if progress < 1.0 else "error"),
            thumbnail=guild.icon.url if guild.icon else None,
            author=ctx.author,
            fields=[
                (f"{t('common.total', ctx=ctx)} {t('general.emojis', ctx=ctx)}", f"**{total_emojis}** / `{max_emojis}`", True),
                ("Static", f"`{static_emojis}`", True),
                ("Animated", f"`{animated_emojis}`", True),
                (t("common.status", ctx=ctx, default="Capacity"), f"{self.progress_bar(progress)} ({round(progress * 100)}%)", False),
                ("Free Slots", f"**{max_emojis - total_emojis}** available", True)
            ]
        )
        await ctx.respond(embed=embed)


def setup(bot: discord.Bot):
    bot.add_cog(EmojiUpload(bot))
