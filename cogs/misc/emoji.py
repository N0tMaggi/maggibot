# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import rarfile
import os
import tempfile
import shutil
from io import BytesIO
import asyncio

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
                return False, "Datei zu klein"

            filename = file_info.filename.lower()
            is_animated = filename.endswith('.gif')
            if not (filename.endswith('.gif') or filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.jpeg')):
                return False, "Ungültiges Format"

            base_name = os.path.basename(filename)
            emoji_name = os.path.splitext(base_name)[0][:30]
            emoji_name = ''.join(c for c in emoji_name if c.isalnum() or c in ('_', '-')).strip()
            if not emoji_name:
                return False, "Ungültiger Name"

            await guild.create_custom_emoji(
                name=emoji_name,
                image=file_data,
                reason=f"Batch-Upload von {ctx.author}",
            )
            return True, "Erfolg"
        except Exception as e:
            return False, str(e)

    @commands.slash_command(
        name="asset-emoji-upload",
        description="Emojis aus einem RAR-Archiv hochladen (Admin only)",
        guild_only=True,
        default_member_permissions=discord.Permissions(manage_emojis_and_stickers=True)
    )
    @commands.has_permissions(manage_emojis_and_stickers=True)
    async def emoji_upload(self, ctx: discord.ApplicationContext, rar_file: discord.Attachment):
        await ctx.defer()

        if not rar_file.filename.lower().endswith('.rar'):
            return await ctx.respond(
                embed=create_error_embed("Ungültiges Dateiformat", "Bitte lade eine **.rar** Datei hoch!"),
                ephemeral=True
            )

        guild = ctx.guild
        max_emojis = guild.emoji_limit
        current_emojis = len(guild.emojis)
        available_slots = max_emojis - current_emojis

        if available_slots <= 0:
            return await ctx.respond(
                embed=create_warning_embed(
                    "Server-Limit erreicht",
                    f"Alle Slots belegt ({max_emojis}/{max_emojis})! Bitte entferne ungenutzte Emojis."
                ),
                ephemeral=True
            )

        try:
            data = await rar_file.read()
            with rarfile.RarFile(BytesIO(data)) as rf:
                valid_files = [f for f in rf.infolist() if not f.isdir() and f.file_size > 0]
                if not valid_files:
                    return await ctx.respond(
                        embed=create_error_embed("Archiv leer", "Keine gültigen Bilddateien im RAR-Archiv gefunden."),
                        ephemeral=True
                    )

                upload_count = min(len(valid_files), available_slots)
                temp_dir = tempfile.mkdtemp()
                success = 0
                skipped = 0
                errors = []

                progress_embed = create_info_embed(
                    "Emoji-Upload gestartet...",
                    f"Verarbeite **{upload_count}** Emojis...\n{self.progress_bar(0)}",
                    fields=[
                        ("Server-Kapazität", f"`{current_emojis}/{max_emojis}`", True),
                        ("Gefundene Dateien", f"`{len(valid_files)}`", True)
                    ]
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
                                f"Upload-Fortschritt ({idx + 1}/{upload_count})",
                                f"{self.progress_bar(progress)}\n\n• Erfolgreich: **{success}**\n• Übersprungen: **{skipped}**"
                            )
                            await ctx.interaction.edit_original_response(embed=embed)
                        await asyncio.sleep(1)
                    except Exception as loop_e:
                        skipped += 1
                        errors.append(f"`{file_info.filename}`: {loop_e}")

                shutil.rmtree(temp_dir, ignore_errors=True)

                res_embed = create_success_embed(
                    "Upload abgeschlossen",
                    f"**{success}** neue Emojis wurden erfolgreich hinzugefügt!",
                    fields=[
                        ("Neuer Server-Status", f"`{current_emojis + success}/{max_emojis}` Emojis", True),
                        ("Übersprungen", f"`{skipped}`", True)
                    ]
                )
                if errors:
                    res_embed.add_field(name="Fehlerdetails", value="\n".join(errors[:5]), inline=False)
                await ctx.interaction.edit_original_response(embed=res_embed)

        except rarfile.BadRarFile:
            await ctx.respond(embed=create_error_embed("Beschädigtes Archiv", "Die Datei konnte nicht als RAR gelesen werden."), ephemeral=True)
        except Exception as e:
            await ctx.respond(embed=create_error_embed("Fehler", str(e)), ephemeral=True)

    @commands.slash_command(
        name="emoji-stats",
        description="Zeigt Statistiken zu den Server-Emojis",
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
            title=f"😄 Emoji-Statistiken • {guild.name}",
            color="success" if progress < 0.8 else ("warning" if progress < 1.0 else "error"),
            thumbnail=guild.icon.url if guild.icon else None,
            author=ctx.author,
            fields=[
                ("Gesamt Emojis", f"**{total_emojis}** / `{max_emojis}`", True),
                ("Statisch", f"`{static_emojis}`", True),
                ("Animiert", f"`{animated_emojis}`", True),
                ("Kapazitätsauslastung", f"{self.progress_bar(progress)} ({round(progress * 100)}%)", False),
                ("Freie Slots", f"**{max_emojis - total_emojis}** Plätze verfügbar", True)
            ]
        )
        await ctx.respond(embed=embed)


def setup(bot: discord.Bot):
    bot.add_cog(EmojiUpload(bot))
