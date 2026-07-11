import discord
from discord.ext import commands
import rarfile
import os
import tempfile
import shutil
from datetime import datetime
from io import BytesIO
import asyncio
from utils.components import build_container, build_view

class EmojiUpload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def progress_bar(self, percentage: float, length: int = 12) -> str:
        filled = 'â–°'
        empty = 'â–±'
        progress = round(percentage * length)
        return f"[{filled * progress}{empty * (length - progress)}] {round(percentage * 100)}%"

    async def process_emoji_file(self, rf, file_info, guild, ctx, temp_dir):
        try:
            file_data = rf.read(file_info)
            
            if len(file_data) < 100: 
                return False, "File too small"

            filename = file_info.filename.lower()
            is_animated = filename.endswith('.gif')
            
            if not (filename.endswith('.gif') or filename.endswith('.png')):
                return False, "Invalid file type"

            base_name = os.path.basename(filename)
            emoji_name = os.path.splitext(base_name)[0][:30]
            emoji_name = ''.join(c for c in emoji_name if c.isalnum() or c in ('_', '-')).strip()
            if not emoji_name:
                return False, "Invalid name"

            await guild.create_custom_emoji(
                name=emoji_name,
                image=file_data,
                reason=f"Uploaded by {ctx.author}",
                animated=is_animated
            )
            return True, "Success"

        except Exception as e:
            return False, str(e)

    @commands.slash_command(
        name="asset-emoji-upload", 
        description="Upload emojis from a RAR archive (Admin only)"
    )
    @commands.has_permissions(administrator=True)
    async def emoji_upload(self, ctx, rar_file: discord.Attachment):
        """Upload emojis from a RAR file (Admin only)"""
        await ctx.defer()
        
        init_container = build_container(
            title="Emoji Upload Initialized",
            description="Starting processing...",
            color="info",
            footer_text=f"Server: {ctx.guild.name} | User: {ctx.author}",
        )
        await ctx.interaction.edit_original_response(
            view=build_view(init_container)
        )

        if not rar_file.filename.lower().endswith('.rar'):
            invalid_file_container = build_container(
                title="Invalid File Type",
                description="Please upload a **.rar** file!",
                color="error",
            )
            return await ctx.interaction.edit_original_response(
                view=build_view(invalid_file_container)
            )

        guild = ctx.guild
        max_emojis = guild.emoji_limit
        current_emojis = len(guild.emojis)
        available_slots = max_emojis - current_emojis
        
        if available_slots <= 0:
            server_full_container = build_container(
                title="Server Full",
                description=f"{max_emojis}/{max_emojis} emoji slots used!",
                color="error",
                fields=[
                    ("Solutions", "- Boost the server\n- Remove old emojis", False),
                ],
            )
            return await ctx.interaction.edit_original_response(
                view=build_view(server_full_container)
            )

        try:
            data = await rar_file.read()
            
            with rarfile.RarFile(BytesIO(data)) as rf:
                valid_files = [
                    f for f in rf.infolist() 
                    if not f.isdir() and f.file_size > 0
                ]

                if not valid_files:
                    no_valid_files_container = build_container(
                        title="No Valid Files",
                        description="The archive contains no valid files!",
                        color="error",
                    )
                    return await ctx.interaction.edit_original_response(
                        view=build_view(no_valid_files_container)
                    )

                upload_count = min(len(valid_files), available_slots)
                total_files = len(valid_files)
                skipped_files = total_files - upload_count

                progress_container = build_container(
                    title="Starting Upload...",
                    description=f"Processing **{upload_count}** emojis\n{self.progress_bar(0)}",
                    color="success",
                    fields=[
                        (
                            "Statistics",
                            f"â€¢ Server Capacity: {current_emojis}/{max_emojis}\n"
                            f"â€¢ Valid Files: {total_files}\n"
                            f"â€¢ To be Skipped: {skipped_files}",
                            False,
                        )
                    ],
                )
                await ctx.interaction.edit_original_response(view=build_view(progress_container))

                success = 0
                skipped = 0
                errors = []
                temp_dir = tempfile.mkdtemp()

                for idx, file_info in enumerate(valid_files[:upload_count]):
                    try:
                        result, message = await self.process_emoji_file(rf, file_info, guild, ctx, temp_dir)
                        
                        if result:
                            success += 1
                        else:
                            skipped += 1
                            errors.append(f"`{file_info.filename}`: {message}")

                        if (idx + 1) % 2 == 0 or (idx + 1) == upload_count:
                            progress = (idx + 1) / upload_count
                            progress_update_container = build_container(
                                title=f"Progress ({idx + 1}/{upload_count})",
                                description=f"{self.progress_bar(progress)}\n"
                                            f"Success: **{success}**\n"
                                            f"Skipped: **{skipped}**",
                                color="success",
                                fields=[
                                    ("Recent Errors", "\n".join(errors[-3:]), False),
                                ] if errors[-5:] else None,
                            )
                            await ctx.interaction.edit_original_response(view=build_view(progress_update_container))
                        
                        await asyncio.sleep(1)  

                    except Exception as e:
                        skipped += 1
                        errors.append(f"`{file_info.filename}`: {str(e)}")
                        continue

                result_container = build_container(
                    title="Upload Complete",
                    description=f"Added **{success}** new emojis!",
                    color="success" if success > 0 else "error",
                    fields=[
                        (
                            "Statistics",
                            f"â€¢ Successful: {success}\n"
                            f"â€¢ Skipped: {skipped}\n"
                            f"â€¢ New Total: {current_emojis + success}/{max_emojis}",
                            False,
                        )
                    ],
                )
                
                if errors:
                    if len(errors) > 5:
                        error_summary = "\n".join(errors[-5:]) + f"\n...and {len(errors) - 5} more"
                    else:
                        error_summary = "\n".join(errors)
                    result_container.add_item(
                        discord.ui.TextDisplay(
                            f"**Error Summary**\n{error_summary}"
                        )
                    )

                await ctx.interaction.edit_original_response(view=build_view(result_container))

                shutil.rmtree(temp_dir)

        except rarfile.BadRarFile:
            corrupted_container = build_container(
                title="Corrupted RAR File",
                description="The provided RAR file is invalid or corrupted!",
                color="error",
            )
            await ctx.interaction.edit_original_response(
                view=build_view(corrupted_container)
            )
        except Exception as e:
            critical_error_container = build_container(
                title="Critical Error",
                description=f"```{str(e)[:1000]}```",
                color="error",
            )
            await ctx.interaction.edit_original_response(
                view=build_view(critical_error_container)
            )


    @commands.slash_command(
        name="emoji-stats", 
        description="Show server emoji statistics"
    )
    async def emoji_stats(self, ctx):
        """Show current emoji statistics"""
        guild = ctx.guild
        max_emojis = guild.emoji_limit
        total_emojis = len(guild.emojis)
        static_emojis = sum(not e.animated for e in guild.emojis)
        animated_emojis = total_emojis - static_emojis
        
        progress = total_emojis / max_emojis if max_emojis > 0 else 0
        color_name = "success" if progress < 0.9 else "warning" if progress < 1 else "error"

        fields = [
            (
                "Counters",
                f"â€¢ Total: **{total_emojis}/{max_emojis}**\n"
                f"â€¢ Static: **{static_emojis}**\n"
                f"â€¢ Animated: **{animated_emojis}**",
                False,
            ),
            (
                "Usage",
                f"{self.progress_bar(progress)}\n{round(progress * 100)}% used",
                False,
            ),
        ]

        if total_emojis >= max_emojis:
            fields.append(("Limit Reached", "No available emoji slots remaining!", False))
        else:
            fields.append(("Free Slots", f"**{max_emojis - total_emojis}** available", False))

        container = build_container(
            title=f"Emoji Statistics for {guild.name}",
            color=color_name,
            fields=fields,
            footer_text=f"Requested by {ctx.author}",
            timestamp=True,
        )
        await ctx.respond(view=build_view(container))

def setup(bot):
    bot.add_cog(EmojiUpload(bot))
