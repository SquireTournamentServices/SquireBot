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

def findGuildRole( a_guild: discord.Guild, a_roleName: str ):
    for role in a_guild.roles:
        if role.name == a_roleName:
           return role
    return ""
    

async def findGuildMember( a_guild: discord.Guild, a_memberName: str ):
    print( f'Looking for {a_memberName}.' )
    async for member in a_guild.fetch_members( ):
        print( f'Found {member}, whose display name is {member.display_name} and whose mention is {member.mention}.' )
        if member.display_name == a_memberName:
            return member
        if member.mention == a_memberName:
            return member
        if member.name == a_memberName:
            return member
        if member.discriminator == a_memberName:
            return member
    return ""
    
def findPlayer( a_guild: discord.Guild, a_tourn: str, a_memberName: str ):
    role = findGuildRole( a_guild, f'{tourn} Player' )
    if role == "":
        return ""
    for member in lyrRole.members:
        if member.display_name == a_memberName:
            return member
        if member.mention == a_memberName:
            return member
        if member.name == a_memberName:
            return member
        if member.discriminator == a_memberName:
            return member
    return ""


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

currentTournaments = {}
closedTournaments = []
playersToBeDropped = []

# When ready, the bot needs to looks at each pre-loaded tournament and add a discord user to each player.
@bot.event
async def on_ready():
    await bot.wait_until_ready( )
    print(f'{bot.user.name} has connected to Discord!')
    guild = bot.guilds[-1]
    print( guild )
    members = [ member.display_name async for member in guild.fetch_members( ) ]
    print( members )
    print( len(guild.members) )
    for tourn in currentTournaments:
        print( f'{tourn} has a guild ID of "{currentTournaments[tourn].guildID}".' )
        guild = bot.get_guild( currentTournaments[tourn].guildID )
        await discord.utils.get( guild.channels, name="general" ).send( "This message is sent from the on_ready method" )
        if type( guild ) != None:
            await currentTournaments[tourn].assignGuild( guild )

























