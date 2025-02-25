import time
import logging
import os
import sys
import discord
from discord.ext import commands
from discord.ext.commands import *


import handlers.env as env

def is_owner(ctx):
    return ctx.author.id == env.get_owner() 