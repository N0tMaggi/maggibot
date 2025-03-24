import discord
from discord.ext import commands
import rarfile
import os
import tempfile
import shutil
from datetime import datetime
from io import BytesIO
import asyncio

class EmojiUpload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def progress_bar(self, percentage: float, length: int = 12) -> str:
        filled = '▰'
        empty = '▱'
        progress = round(percentage * length)
        return f"[{filled * progress}{empty * (length - progress)}] {round(percentage * 100)}%"

    async def process_emoji_file(self, rf, file_info, guild, ctx, temp_dir):
        try:
            # Extrahiere die Datei direkt in den Speicher
            file_data = rf.read(file_info)
            
            # Überprüfe die Mindestdateigröße
            if len(file_data) < 100:  # 100 Bytes Minimum
                return False, "File too small"

            # Dateinamen und Erweiterung verarbeiten
            filename = file_info.filename.lower()
            is_animated = filename.endswith('.gif')
            
            # Dateierweiterung validieren
            if not (filename.endswith('.gif') or filename.endswith('.png')):
                return False, "Invalid file type"

            # Erstelle einen sicheren Emoji-Namen
            base_name = os.path.basename(filename)
            emoji_name = os.path.splitext(base_name)[0][:30]
            emoji_name = ''.join(c for c in emoji_name if c.isalnum() or c in ('_', '-')).strip()
            if not emoji_name:
                return False, "Invalid name"

            # Erstelle das Emoji
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
        
        # Initial response
        await ctx.interaction.edit_original_response(
            embed=discord.Embed(
                title="Emoji Upload Initialized",
                description="Starting processing...",
                color=discord.Color.blue()
            ).set_footer(text=f"Server: {ctx.guild.name} | User: {ctx.author}")
        )

        # Validate file type
        if not rar_file.filename.lower().endswith('.rar'):
            return await ctx.interaction.edit_original_response(
                embed=discord.Embed(
                    title="Invalid File Type",
                    description="Please upload a **.rar** file!",
                    color=discord.Color.red()
                )
            )

        # Check emoji limits
        guild = ctx.guild
        max_emojis = guild.emoji_limit
        current_emojis = len(guild.emojis)
        available_slots = max_emojis - current_emojis
        
        if available_slots <= 0:
            return await ctx.interaction.edit_original_response(
                embed=discord.Embed(
                    title="Server Full",
                    description=f"{max_emojis}/{max_emojis} emoji slots used!",
                    color=discord.Color.red()
                ).add_field(
                    name="Solutions",
                    value="- Boost the server\n- Remove old emojis",
                    inline=False
                )
            )

        try:
            # Read RAR file into memory
            data = await rar_file.read()
            
            # Process archive in memory
            with rarfile.RarFile(BytesIO(data)) as rf:
                valid_files = [
                    f for f in rf.infolist() 
                    if not f.isdir() and f.file_size > 0
                ]

                if not valid_files:
                    return await ctx.interaction.edit_original_response(
                        embed=discord.Embed(
                            title="No Valid Files",
                            description="The archive contains no valid files!",
                            color=discord.Color.red()
                        )
                    )

                # Calculate upload limits
                upload_count = min(len(valid_files), available_slots)
                total_files = len(valid_files)
                skipped_files = total_files - upload_count

                # Show initial stats
                progress_embed = discord.Embed(
                    title="Starting Upload...",
                    description=f"Processing **{upload_count}** emojis\n{self.progress_bar(0)}",
                    color=discord.Color.green()
                )
                progress_embed.add_field(
                    name="Statistics",
                    value=f"• Server Capacity: {current_emojis}/{max_emojis}\n"
                          f"• Valid Files: {total_files}\n"
                          f"• To be Skipped: {skipped_files}",
                    inline=False
                )
                await ctx.interaction.edit_original_response(embed=progress_embed)

                success = 0
                skipped = 0
                errors = []
                temp_dir = tempfile.mkdtemp()

                for idx, file_info in enumerate(valid_files[:upload_count]):
                    try:
                        # Verarbeite jede Datei
                        result, message = await self.process_emoji_file(rf, file_info, guild, ctx, temp_dir)
                        
                        if result:
                            success += 1
                        else:
                            skipped += 1
                            errors.append(f"`{file_info.filename}`: {message}")

                        # Update progress
                        if (idx + 1) % 2 == 0 or (idx + 1) == upload_count:
                            progress = (idx + 1) / upload_count
                            embed = discord.Embed(
                                title=f"Progress ({idx + 1}/{upload_count})",
                                description=f"{self.progress_bar(progress)}\n"
                                            f"Success: **{success}**\n"
                                            f"Skipped: **{skipped}**",
                                color=discord.Color.green()
                            )
                            if errors[-5:]:
                                embed.add_field(
                                    name="Recent Errors",
                                    value="\n".join(errors[-3:]),
                                    inline=False
                                )
                            await ctx.interaction.edit_original_response(embed=embed)
                        
                        await asyncio.sleep(1)  # Rate Limit Schutz

                    except Exception as e:
                        skipped += 1
                        errors.append(f"`{file_info.filename}`: {str(e)}")
                        continue

                # Final result embed
                result_embed = discord.Embed(
                    title="Upload Complete",
                    description=f"Added **{success}** new emojis!",
                    color=discord.Color.green() if success > 0 else discord.Color.red()
                )
                result_embed.add_field(
                    name="Statistics",
                    value=f"• Successful: {success}\n"
                          f"• Skipped: {skipped}\n"
                          f"• New Total: {current_emojis + success}/{max_emojis}",
                    inline=False
                )
                
                if errors:
                    result_embed.add_field(
                        name="Error Summary",
                        value="\n".join(errors[-5:]) + f"\n...and {len(errors)-5} more" if len(errors) > 5 else "\n".join(errors),
                        inline=False
                    )

                await ctx.interaction.edit_original_response(embed=result_embed)

                # Cleanup
                shutil.rmtree(temp_dir)

        except rarfile.BadRarFile:
            await ctx.interaction.edit_original_response(
                embed=discord.Embed(
                    title="Corrupted RAR File",
                    description="The provided RAR file is invalid or corrupted!",
                    color=discord.Color.red()
                )
            )
        except Exception as e:
            await ctx.interaction.edit_original_response(
                embed=discord.Embed(
                    title="Critical Error",
                    description=f"```{str(e)[:1000]}```",
                    color=discord.Color.red()
                )
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
        color = discord.Color.green() if progress < 0.9 else discord.Color.orange() if progress < 1 else discord.Color.red()
        
        embed = discord.Embed(
            title=f"Emoji Statistics for {guild.name}",
            color=color,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Counters",
            value=f"• Total: **{total_emojis}/{max_emojis}**\n"
                  f"• Static: **{static_emojis}**\n"
                  f"• Animated: **{animated_emojis}**",
            inline=False
        )
        
        embed.add_field(
            name="Usage",
            value=f"{self.progress_bar(progress)}\n{round(progress * 100)}% used",
            inline=False
        )
        
        if total_emojis >= max_emojis:
            embed.add_field(
                name="Limit Reached",
                value="No available emoji slots remaining!",
                inline=False
            )
        else:
            embed.add_field(
                name="Free Slots",
                value=f"**{max_emojis - total_emojis}** available",
                inline=False
            )
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(EmojiUpload(bot))
