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
            
            # Process archive in memory using a BytesIO stream
            with rarfile.RarFile(BytesIO(data)) as rf:
                # Filter valid files
                valid_files = [
                    f for f in rf.infolist() 
                    if not f.isdir() and f.filename.lower().endswith(('.gif', '.png'))
                ]

                if not valid_files:
                    return await ctx.interaction.edit_original_response(
                        embed=discord.Embed(
                            title="No Valid Files",
                            description="The archive contains no PNG or GIF files!",
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

                # Create a temporary directory to extract files
                temp_dir = tempfile.mkdtemp()

                success = 0
                skipped = 0
                for idx, file_info in enumerate(valid_files[:upload_count]):
                    try:
                        # Extract file to temporary directory
                        rf.extract(file_info, path=temp_dir)
                        extracted_path = os.path.join(temp_dir, file_info.filename)
                        # Read file data from the extracted file
                        with open(extracted_path, 'rb') as f:
                            emoji_data = f.read()

                        # Validate size (max 256 KB)
                        if len(emoji_data) > 256 * 1024:
                            skipped += 1
                            continue

                        # Create a sanitized name (max 31 characters)
                        base_name = os.path.basename(file_info.filename)
                        emoji_name = os.path.splitext(base_name)[0][:31]
                        emoji_name = ''.join(c for c in emoji_name if c.isalnum() or c in ('_', '-'))

                        # Upload emoji to the guild
                        await guild.create_custom_emoji(
                            name=emoji_name,
                            image=emoji_data,
                            reason=f"Uploaded by {ctx.author}"
                        )
                        success += 1

                        # Update progress every 5 files or on the final file
                        if (idx + 1) % 5 == 0 or (idx + 1) == upload_count:
                            progress = (idx + 1) / upload_count
                            embed = discord.Embed(
                                title=f"Progress ({idx + 1}/{upload_count})",
                                description=f"{self.progress_bar(progress)}\n"
                                            f"Success: **{success}**\n"
                                            f"Skipped: **{skipped}**",
                                color=discord.Color.green()
                            )
                            await ctx.interaction.edit_original_response(embed=embed)
                        
                        # Small delay to help avoid rate limits
                        await asyncio.sleep(0.5)

                    except Exception as e:
                        skipped += 1
                        print(f"Error processing {file_info.filename}: {e}")

                # Clean up temporary directory
                shutil.rmtree(temp_dir)

                # Final result embed
                result_embed = discord.Embed(
                    title="Upload Complete",
                    description=f"Added **{success}** new emojis!",
                    color=discord.Color.green()
                )
                result_embed.add_field(
                    name="Statistics",
                    value=f"• Successful: {success}\n"
                          f"• Skipped: {skipped}\n"
                          f"• New Total: {current_emojis + success}/{max_emojis}",
                    inline=False
                )
                await ctx.interaction.edit_original_response(embed=result_embed)

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
