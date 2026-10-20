# -*- coding: utf-8 -*-
"""
Tests for Tags cog and TagCreateModal.
"""

import pytest
import discord
from unittest.mock import MagicMock, AsyncMock

from cogs.server.tags import Tags, TagCreateModal
import handlers.config as config


@pytest.fixture
def tags_cog(mock_bot):
    cog = Tags(mock_bot)
    cog.tag.cog = cog
    cog.tag_add.cog = cog
    cog.tag_remove.cog = cog
    cog.tag_list.cog = cog
    return cog


@pytest.fixture
def mock_interaction(mock_guild, mock_member):
    interaction = MagicMock(spec=discord.Interaction)
    interaction.guild = mock_guild
    interaction.user = mock_member
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


class TestTagCreation:
    @pytest.mark.asyncio
    async def test_tag_add_opens_modal(self, temp_json_env, tags_cog, mock_context):
        """Test tag-add command triggers send_modal when tag doesn't exist."""
        mock_context.send_modal = AsyncMock()

        await tags_cog.tag_add(mock_context, "rules")

        mock_context.send_modal.assert_awaited_once()
        modal = mock_context.send_modal.call_args[0][0]
        assert isinstance(modal, TagCreateModal)
        assert modal.tag_name == "rules"

    @pytest.mark.asyncio
    async def test_tag_add_already_exists_warning(self, temp_json_env, tags_cog, mock_context):
        """Test tag-add command warns if tag already exists."""
        gid = str(mock_context.guild.id)
        tags_cog.tags[gid] = {"rules": "Some rules"}

        await tags_cog.tag_add(mock_context, "rules")

        mock_context.respond.assert_awaited_once()
        call_kwargs = mock_context.respond.call_args[1]
        assert "embed" in call_kwargs
        assert call_kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_modal_callback_creates_tag(self, temp_json_env, tags_cog, mock_interaction):
        """Test modal submission saves the tag into cog.tags and disk."""
        gid = mock_interaction.guild.id
        modal = TagCreateModal("welcome", tags_cog, gid)
        modal.content_input.value = "Welcome to {servername}, {user}!"

        await modal.callback(mock_interaction)

        gid_str = str(gid)
        assert gid_str in tags_cog.tags
        assert tags_cog.tags[gid_str]["welcome"] == "Welcome to {servername}, {user}!"

        stored = config.load_tags()
        assert stored[gid_str]["welcome"] == "Welcome to {servername}, {user}!"

        mock_interaction.response.send_message.assert_awaited_once()
        call_kwargs = mock_interaction.response.send_message.call_args[1]
        assert "embed" in call_kwargs
        assert call_kwargs.get("ephemeral") is True


class TestTagRetrievalAndReplacements:
    @pytest.mark.asyncio
    async def test_tag_with_author_replacement(self, temp_json_env, tags_cog, mock_context):
        """Test tag retrieval replacing {user} with author mention and {servername}."""
        gid = str(mock_context.guild.id)
        tags_cog.tags[gid] = {"info": "Hello {user}, welcome to {servername}!"}

        await tags_cog.tag(mock_context, "info")

        expected = f"Hello {mock_context.author.mention}, welcome to {mock_context.guild.name}!"
        mock_context.respond.assert_awaited_once_with(expected)

    @pytest.mark.asyncio
    async def test_tag_with_target_user_replacement(self, temp_json_env, tags_cog, mock_context):
        """Test tag retrieval replacing {user} with specified target member."""
        gid = str(mock_context.guild.id)
        tags_cog.tags[gid] = {"hello": "Hey {user}!"}

        target_member = MagicMock(spec=discord.Member)
        target_member.mention = "<@777888>"

        await tags_cog.tag(mock_context, "hello", user=target_member)

        mock_context.respond.assert_awaited_once_with("Hey <@777888>!")

    @pytest.mark.asyncio
    async def test_tag_case_insensitive_lookup(self, temp_json_env, tags_cog, mock_context):
        """Test tag lookup matches case-insensitively."""
        gid = str(mock_context.guild.id)
        tags_cog.tags[gid] = {"CustomTag": "Tag content"}

        await tags_cog.tag(mock_context, "customtag")

        mock_context.respond.assert_awaited_once_with("Tag content")

    @pytest.mark.asyncio
    async def test_tag_not_found(self, temp_json_env, tags_cog, mock_context):
        """Test retrieving a non-existent tag responds with error embed."""
        await tags_cog.tag(mock_context, "nonexistent")

        mock_context.respond.assert_awaited_once()
        call_kwargs = mock_context.respond.call_args[1]
        assert "embed" in call_kwargs
        assert call_kwargs.get("ephemeral") is True


class TestTagDeletion:
    @pytest.mark.asyncio
    async def test_tag_remove_success(self, temp_json_env, tags_cog, mock_context):
        """Test deleting an existing tag removes it from storage."""
        gid = str(mock_context.guild.id)
        tags_cog.tags[gid] = {"tag1": "content1", "tag2": "content2"}

        await tags_cog.tag_remove(mock_context, "tag1")

        assert "tag1" not in tags_cog.tags.get(gid, {})
        assert "tag2" in tags_cog.tags[gid]
        assert "tag1" not in config.load_tags().get(gid, {})

        mock_context.respond.assert_awaited_once()
        call_kwargs = mock_context.respond.call_args[1]
        assert "embed" in call_kwargs

    @pytest.mark.asyncio
    async def test_tag_remove_last_tag_cleans_guild_entry(self, temp_json_env, tags_cog, mock_context):
        """Test removing the last tag deletes the guild entry entirely."""
        gid = str(mock_context.guild.id)
        tags_cog.tags[gid] = {"solotag": "content"}

        await tags_cog.tag_remove(mock_context, "solotag")

        assert gid not in tags_cog.tags
        assert gid not in config.load_tags()

    @pytest.mark.asyncio
    async def test_tag_remove_not_found(self, temp_json_env, tags_cog, mock_context):
        """Test deleting a non-existent tag returns an error embed."""
        await tags_cog.tag_remove(mock_context, "missing_tag")

        mock_context.respond.assert_awaited_once()
        call_kwargs = mock_context.respond.call_args[1]
        assert "embed" in call_kwargs
        assert call_kwargs.get("ephemeral") is True


class TestTagListing:
    @pytest.mark.asyncio
    async def test_tag_list_empty(self, temp_json_env, tags_cog, mock_context):
        """Test listing tags when guild has none."""
        await tags_cog.tag_list(mock_context)

        mock_context.respond.assert_awaited_once()
        call_kwargs = mock_context.respond.call_args[1]
        assert "embed" in call_kwargs
        assert call_kwargs.get("ephemeral") is True

    @pytest.mark.asyncio
    async def test_tag_list_populated(self, temp_json_env, tags_cog, mock_context):
        """Test listing tags when guild has multiple tags."""
        gid = str(mock_context.guild.id)
        tags_cog.tags[gid] = {"zebra": "1", "alpha": "2", "beta": "3"}

        await tags_cog.tag_list(mock_context)

        mock_context.respond.assert_awaited_once()
        call_kwargs = mock_context.respond.call_args[1]
        embed = call_kwargs["embed"]
        assert "alpha" in embed.description
        assert "beta" in embed.description
        assert "zebra" in embed.description
