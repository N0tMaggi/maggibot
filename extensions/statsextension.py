# -*- coding: utf-8 -*-
import discord
from utils.embed_helpers import create_embed


def create_stats_embed(title, description="", color_type="stats", author=None, **kwargs):
    return create_embed(
        title=title,
        description=description,
        color=color_type,
        author=author,
        footer_text="Maggi Stats System",
        footer_icon="https://maggi.dev/favicon/favicon.ico",
        **kwargs
    )
