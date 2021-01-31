import os


import discord
from discord import Activity, ActivityType
from discord.ext import commands
from dotenv import load_dotenv


from Tournament import *


async def isPrivateMessage( ctx, send: bool = True ) -> bool:
    digest = (str(ctx.message.channel.type) == 'private')
    if digest and send:
        await ctx.send( f'In general, you are not allowed to send commands via DM. Each tournament is tied to a server. Please send this message from the appropriate server.' )
    return digest

async def isTournamentAdmin( ctx, send: bool = True ) -> bool:
    digest = False
    adminMention = getTournamentAdminMention( ctx.message.guild )
    for role in ctx.message.author.roles:
        digest |= str(role).lower() == "tournament admin"
    if not digest and send:
        await ctx.send( f'{ctx.message.author.mention}, you do not admin permissions for tournaments on this server. Please do not do this again or {adminMention} may intervene.' )
    return digest

async def checkTournExists( tourn, ctx, send: bool = True ):
    digest = ( tourn in currentTournaments )
    if not digest and send:
        await ctx.send( f'{ctx.message.author.mention}, there is not a tournament named "{tourn}" in this server.' )
    return digest

async def correctGuild( tourn, ctx, send: bool = True ):
    digest = ( currentTournaments[tourn].hostGuildName == ctx.message.guild.name )
    if not digest and send:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} does not belong to this server. Please send this command from the correct server.' )
    return digest

async def isTournDead( tourn, ctx, send: bool = True ):
    adminMetnion = getTournamentAdminMention( ctx.message.guild )
    digest = currentTournaments[tourn].isDead( )
    if digest and send:
        await ctx.send( f'{ctx.message.author.mention}, {tourn} has either ended or been cancelled. Check with {adminMention} if you think this is an error.' )
    return digest

def getTournamentAdminMention( a_guild ) -> str:
    adminMention = ""
    for role in a_guild.roles:
        if str(role).lower() == "tournament admin":
            adminMention = role.mention
            break
    return adminMention

def currentGuildTournaments( a_guildName: str ):
    tourns = {}
    for tourn in currentTournaments:
        if not currentTournaments[tourn].isDead() and currentTournaments[tourn].hostGuildName == a_guildName:
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
        if member.mention == a_memberName:
            return member
    return ""
    
def findPlayer( a_guild: discord.Guild, a_tourn: str, a_memberName: str ):
    role = discord.utils.get( a_guild.roles, name=f'{a_tourn} Player' )
    if type( role ) != discord.Role:
        return ""
    for member in role.members:
        if member.display_name == a_memberName:
            return member
        if member.mention == a_memberName:
            return member
        if f'<@!{member.id}>' == a_memberName:
            return member
        if f'<@{member.id}>' == a_memberName:
            return member
    return ""

def splitMessage( msg: str, limit: int = 2000, delim: str = "\n" ) -> List[str]:
    if len(msg) <= limit:
        return [ msg ]
    msg = msg.split( delim )
    digest = [ "" ]
    for submsg in msg:
        if len(digest[-1]) + len(submsg) <= limit:
            digest[-1] += delim + submsg
        else:
            digest.append( submsg )
    return digest
    


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
            currentTournaments[tourn].loop = bot.loop


def message_to_xml( msg: discord.Message, indent: str = "" ) -> str:
    digest  = f'{indent}<message author="{msg.author}" time="{msg.created_at}">\n'
    digest += f'{indent*2}<text>{msg.content}</text>\n'
    digest += f'{indent}</message>\n'
    return digest

@bot.command(name='test')
async def test( ctx, *args ):
    w1 = 7
    w2 = max( [ len(m.display_name) for m in ctx.message.channel.members ] ) + 2
    w3 = max( [ len(str(m.id)) for m in ctx.message.channel.members ] ) + 2
    for member in ctx.message.channel.members:
        print( f'{str(member.display_name == member.name).ljust(w1)}{member.display_name.ljust(w2)}{str(member.id).ljust(w3)}{member.mention}' )
    print( args )
    print( findPlayer( ctx.message.guild, "Izzet", args[0] ) )
    
    

@bot.command(name='scrape')
async def adminPlayerProfile( ctx ):
    messages = await ctx.message.channel.history( limit=100000, oldest_first=True ).flatten( )
    with open( "scrapTest.xml", "w" ) as f:
        f.write( "<history>\n" )
        for msg in messages:
            f.write( message_to_xml( msg, "\t" ) )
        f.write( "</history>" )
    print( f'A total of {len(messages)} messages were scrapped.' )






