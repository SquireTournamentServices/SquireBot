import os


import discord
from discord import Activity, ActivityType
from discord.ext import commands
from dotenv import load_dotenv


from Tournament import *


def isPrivateMessage( a_message ) -> bool:
    return str(a_message.channel.type) == 'private'
    
def isTournamentAdmin( a_author ) -> bool:
    retValue = False
    for role in a_author.roles:
        retValue |= str(role).lower() == "tournament admin"
    return retValue

def getTournamentAdminMention( a_guild ) -> str:
    adminMention = ""
    for role in a_guild.roles:
        if str(role).lower() == "tournament admin":
            adminMention = role.mention
            break
    return adminMention

def futureGuildTournaments( a_guildName ):
    tourns = {}
    for tourn in currentTournaments:
        if currentTournaments[tourn].isPlanned() and currentTournaments[tourn].hostGuildName == a_guildName:
            tourns[tourn] = currentTournaments[tourn]
    return tourns

def activeGuildTournaments( a_guildName ):
    tourns = {}
    for tourn in currentTournaments:
        if currentTournaments[tourn].isActive() and currentTournaments[tourn].hostGuildName == a_guildName:
            tourns[tourn] = currentTournaments[tourn]
    return tourns
    

def hasStartedTournament( a_guildName ) -> bool:
    for tourn in currentTournaments:
        if currentTournaments[tourn].tournStarted and currentTournaments[tourn].hostGuildName == a_guildName:
            return True
    return False

def findGuildRole( a_guild: discord.Guild, a_roleName: str ):
    for role in a_guild.roles:
        if role.name == a_roleName:
           return role
    return ""
    

def findGuildMember( a_guild: discord.Guild, a_memberName: str ):
    print( f'Looking for {a_memberName}.' )
    for member in a_guild.members:
        print( f'Found {member}, whose display name is {member.display_name} and whose mention is {member.mention}.' )
        if member.display_name == a_memberName:
            return member
        if member.mention == a_memberName:
            return member
    return ""
    
def findPlayer( a_guild: discord.Guild, a_tourn: str, a_memberName: str ):
    role = findGuildRole( a_guild, f'{a_tourn} Player' )
    if role == "":
        return ""
    for member in role.members:
        if member.display_name == a_memberName:
            return member
        if member.mention == a_memberName:
            return member
    return ""


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

currentTournaments = {}
closedTournaments = []
playersToBeDropped = []

# When ready, the bot needs to looks at each pre-loaded tournament and add a discord user to each player.
@bot.event
async def on_ready():
    await bot.wait_until_ready( )
    print(f'{bot.user.name} has connected to Discord!')
    for tourn in currentTournaments:
        print( f'{tourn} has a guild ID of "{currentTournaments[tourn].guildID}".' )
        guild = bot.get_guild( currentTournaments[tourn].guildID )
        if type( guild ) != None:
            currentTournaments[tourn].assignGuild( guild )


@bot.command(name='test')
async def adminPlayerProfile( ctx ):
    await ctx.send( f'There are {len(currentTournaments)} planned.' )























