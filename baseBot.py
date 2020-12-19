import os


import discord.member
import discord.guild
from discord import Activity, ActivityType
from discord.ext import commands
from dotenv import load_dotenv


from tournament.match import match
from tournament.deck import deck
from tournament.player import player
from tournament.tournament import tournament
from tournament.tournamentUtils import *


def isPrivateMessage( a_message ) -> bool:
    return str(a_message.channel.type) == 'private'
    
def isTournamentAdmin( a_author ) -> bool:
    retValue = False
    for role in a_author.roles:
        retValue |= str(role).lower() == "tournament admin"
    return retValue

def getTournamentAdminMention( a_guild ) -> str:
    adminMention = "tournament admin"
    for role in a_guild.roles:
        if str(role).lower() == "tournament admin":
            adminMention = role.mention
    return adminMention

def futureGuildTournaments( a_guildName ):
    tourns = {}
    for tourn in currentTournaments:
        if currentTournaments[tourn].isPlanned() and currentTournaments[tourn].hostGuildName == a_guildName:
            tourns[tourn] = currentTournaments[tourn]
    return tourns

def hasStartedTournament( a_guildName ) -> bool:
    for tourn in currentTournaments:
        if currentTournaments[tourn].tournStarted and currentTournaments[tourn].hostGuildName == a_guildName:
            return True
    return False

def findGuildMember( a_guild: discord.Guild, a_memberName: str ):
    for member in a_guild.members:
        if member.display_name == a_memberName:
            return member
    return ""
    


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

# When ready, the bot needs to looks at each pre-loaded tournament and add a discord user to each player.
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    print( bot.guilds )


currentTournaments = {}
closedTournaments = []

