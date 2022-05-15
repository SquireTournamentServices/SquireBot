#![allow(unused_imports, dead_code, unused_variables)]

mod misc_commands;
mod model;
mod setup_commands;
mod tournament_commands;
mod utils;

use squire_core;

use model::{
    confirmations::{confirmation::Confirmation, confirmation_map::ConfirmationsContainer},
    consts::*,
    guild_settings::{GuildSettings, GuildSettingsContainer},
    guild_tournaments::{GuildTournaments, GuildTournamentsContainer},
    misfortune::*,
    squire_tournament::SquireTournament,
    tournament_container::TournamentContainer,
};
use misc_commands::{flip_coins::*, group::MISCCOMMANDS_GROUP};
use setup_commands::{group::SETUPCOMMANDS_GROUP, setup::*};
use tournament_commands::group::TOURNAMENTCOMMANDS_GROUP;

use dashmap::DashMap;
use dotenv::vars;
use serde_json;
use serenity::{
    prelude::*,
    async_trait,
    framework::standard::{
        help_commands,
        macros::{check, command, group, help, hook},
        Args, CommandGroup, CommandOptions, CommandResult, Delimiter, DispatchError, HelpOptions,
        Reason, StandardFramework,
    },
    http::Http,
    model::{
        channel::{
            Channel, ChannelCategory, ChannelType, Embed, EmbedField, GuildChannel, Message,
        },
        gateway::GatewayIntents,
        gateway::Ready,
        guild::{Guild, Role},
        id::{GuildId, RoleId, UserId},
        permissions::Permissions,
    },
};
use tokio::sync::Mutex;

use std::{
    collections::{HashMap, HashSet},
    fmt::Write,
    fs::read_to_string,
    sync::{Arc, RwLock},
};

struct Handler;

#[async_trait]
impl EventHandler for Handler {
    async fn ready(&self, _: Context, ready: Ready) {
        println!("{} is connected!", ready.user.name);
    }

    async fn guild_create(&self, ctx: Context, guild: Guild, _: bool) {
        println!("Look, a guild: {}", guild.name);
        let data = ctx.data.read().await;
        let all_settings = data.get::<GuildSettingsContainer>().unwrap();
        if let Some(mut settings) = all_settings.get_mut(&guild.id) {
            settings.update(&guild);
        } else {
            let settings = GuildSettings::from_existing(&guild);
            println!("{:#?}", settings);
            all_settings.insert(guild.id.clone(), settings);
        }
        std::fs::write(
            "guild_settings.json",
            serde_json::to_string(&all_settings).expect("Failed to serialize guild settings."),
        )
            .expect("Failed to save guild settings json.");
        }

    async fn category_create(&self, ctx: Context, new: &ChannelCategory) {
        let data = ctx.data.read().await;
        let all_settings = data.get::<GuildSettingsContainer>().unwrap();
        if let Some(mut settings) = all_settings.get_mut(&new.guild_id) {
            match settings.matches_category {
                None => {
                    if new.name == DEFAULT_MATCHES_CATEGORY_NAME {
                        settings.matches_category = Some(new.id);
                    }
                }
                Some(_) => {}
            }
        }
        ()
    }

    async fn category_delete(&self, ctx: Context, category: &ChannelCategory) {
        let data = ctx.data.read().await;
        let all_settings = data.get::<GuildSettingsContainer>().unwrap();
        if let Some(mut settings) = all_settings.get_mut(&category.guild_id) {
            match settings.matches_category {
                Some(c) => {
                    if c == category.id {
                        settings.matches_category = None;
                    }
                }
                None => {}
            }
        }
        ()
    }

    async fn channel_create(&self, ctx: Context, new: &GuildChannel) {
        let data = ctx.data.read().await;
        let all_settings = data.get::<GuildSettingsContainer>().unwrap();
        if let Some(mut settings) = all_settings.get_mut(&new.guild_id) {
            match settings.pairings_channel {
                None => {
                    if new.name == DEFAULT_PAIRINGS_CHANNEL_NAME {
                        settings.pairings_channel = Some(new.id);
                    }
                }
                Some(c) => {}
            }
        }
        ()
    }

    async fn channel_delete(&self, ctx: Context, channel: &GuildChannel) {
        let data = ctx.data.read().await;
        let all_settings = data.get::<GuildSettingsContainer>().unwrap();
        if let Some(mut settings) = all_settings.get_mut(&channel.guild_id) {
            match settings.pairings_channel {
                Some(c) => {
                    if c == channel.id {
                        settings.pairings_channel = None;
                    }
                }
                None => {}
            }
        }
        ()
    }

    // NOTE: This covers both categories and guild channels
    async fn channel_update(&self, ctx: Context, _: Option<Channel>, new: Channel) {
        let data = ctx.data.read().await;
        let all_settings = data.get::<GuildSettingsContainer>().unwrap();
        match new {
            Channel::Guild(c) => {
                if c.kind == ChannelType::Text && c.name == DEFAULT_PAIRINGS_CHANNEL_NAME {
                    if let Some(mut settings) = all_settings.get_mut(&c.guild_id) {
                        match settings.pairings_channel {
                            None => {
                                settings.pairings_channel = Some(c.id);
                            }
                            Some(c) => {}
                        }
                    }
                }
            }
            Channel::Category(c) => {
                if c.name == DEFAULT_MATCHES_CATEGORY_NAME {
                    if let Some(mut settings) = all_settings.get_mut(&c.guild_id) {
                        match settings.matches_category {
                            None => {
                                settings.matches_category = Some(c.id);
                            }
                            Some(_) => {}
                        }
                    }
                }
            }
            _ => {}
        }
        ()
    }

    async fn guild_role_create(&self, ctx: Context, new: Role) {
        let data = ctx.data.read().await;
        let all_settings = data.get::<GuildSettingsContainer>().unwrap();
        if let Some(mut settings) = all_settings.get_mut(&new.guild_id) {
            match new.name.as_str() {
                DEFAULT_JUDGE_ROLE_NAME => {
                    if settings.judge_role.is_none() {
                        settings.judge_role = Some(new.id);
                    }
                }
                DEFAULT_TOURN_ADMIN_ROLE_NAME => {
                    if settings.tourn_admin_role.is_none() {
                        settings.tourn_admin_role = Some(new.id);
                    }
                }
                _ => {}
            }
        }
        ()
    }

    async fn guild_role_update(&self, ctx: Context, _: Option<Role>, new: Role) {
        let data = ctx.data.read().await;
        let all_settings = data.get::<GuildSettingsContainer>().unwrap();
        if let Some(mut settings) = all_settings.get_mut(&new.guild_id) {
            match new.name.as_str() {
                DEFAULT_JUDGE_ROLE_NAME => {
                    if settings.judge_role.is_none() {
                        settings.judge_role = Some(new.id);
                    }
                }
                DEFAULT_TOURN_ADMIN_ROLE_NAME => {
                    if settings.tourn_admin_role.is_none() {
                        settings.tourn_admin_role = Some(new.id);
                    }
                }
                _ => {
                    // Makes sure that the tournament admin and judge roles aren't renamed.
                    match settings.judge_role {
                        Some(id) => {
                            if new.id == id {
                                settings.judge_role = None;
                            }
                        }
                        None => {}
                    }
                    match settings.tourn_admin_role {
                        Some(id) => {
                            if new.id == id {
                                settings.tourn_admin_role = None;
                            }
                        }
                        None => {}
                    }
                }
            }
        }
        ()
    }

    async fn guild_role_delete(
        &self,
        ctx: Context,
        guild_id: GuildId,
        removed_role: RoleId,
        _: Option<Role>,
    ) {
        let data = ctx.data.read().await;
        let all_settings = data.get::<GuildSettingsContainer>().unwrap();
        if let Some(mut settings) = all_settings.get_mut(&guild_id) {
            match settings.judge_role {
                Some(id) => {
                    if id == removed_role {
                        settings.judge_role = Some(id);
                    }
                }
                None => {}
            }
            match settings.tourn_admin_role {
                Some(id) => {
                    if id == removed_role {
                        settings.tourn_admin_role = Some(id);
                    }
                }
                None => {}
            }
        }
        ()
    }
}

// The framework provides two built-in help commands for you to use.
// But you can also make your own customized help command that forwards
// to the behaviour of either of them.
#[help("squirebot-help")]
#[individual_command_tip = "SquireBot Commands:\nIf you want more information about a specific command, just pass the command as argument."]
async fn my_help(
    context: &Context,
    msg: &Message,
    args: Args,
    help_options: &'static HelpOptions,
    groups: &[&'static CommandGroup],
    owners: HashSet<UserId>,
) -> CommandResult {
    let _ = help_commands::with_embeds(context, msg, args, help_options, groups, owners).await;
    Ok(())
}

#[hook]
async fn before_command(ctx: &Context, msg: &Message, _command_name: &str) -> bool {
    true
}

#[hook]
async fn after_command(
    _ctx: &Context,
    _msg: &Message,
    command_name: &str,
    command_result: CommandResult,
) {
    match command_result {
        Ok(()) => println!("Processed command '{}'", command_name),
        Err(why) => println!("Command '{}' returned error {:?}", command_name, why),
    }
}

#[tokio::main]
async fn main() {
    // Configure the client with your Discord bot token in the environment.
    let env_vars: HashMap<String, String> = dotenv::vars().collect();
    let token = env_vars
        .get("TESTING_TOKEN")
        .expect("Expected a token in the environment");

    let http = Http::new_with_token(&token);

    // We will fetch your bot's owners and id
    let (owners, bot_id) = match http.get_current_application_info().await {
        Ok(info) => {
            let mut owners = HashSet::new();
            if let Some(team) = info.team {
                owners.insert(team.owner_user_id);
            } else {
                owners.insert(info.owner.id);
            }
            match http.get_current_user().await {
                Ok(bot_id) => (owners, bot_id.id),
                Err(why) => panic!("Could not access the bot id: {:?}", why),
            }
        }
        Err(why) => panic!("Could not access application info: {:?}", why),
    };

    let framework = StandardFramework::new()
        .configure(|c| {
            c.with_whitespace(true)
                .on_mention(Some(bot_id))
                .prefix("!")
                .delimiters(vec![", ", ","])
                .owners(owners)
        })
    .before(before_command)
        .after(after_command)
        .help(&MY_HELP)
        .group(&SETUPCOMMANDS_GROUP)
        .group(&TOURNAMENTCOMMANDS_GROUP)
        .group(&MISCCOMMANDS_GROUP);

    let mut intents = GatewayIntents::empty();
    intents.guilds();
    intents.insert(GatewayIntents::GUILD_MESSAGES);
    intents.direct_messages();

    let mut client = Client::builder(&token)
        .event_handler(Handler)
        .framework(framework)
        .intents(GatewayIntents::all())
        .await
        .expect("Err creating client");

    {
        let mut data = client.data.write().await;

        // Construct the default settings for a guild, stored in the json file.
        let all_guild_settings: DashMap<GuildId, GuildSettings> = serde_json::from_str(
            &mut read_to_string("./guild_settings.json").expect("Guilds settings file not found."),
        )
            .expect("The guild settings data is malformed.");
        data.insert::<GuildSettingsContainer>(all_guild_settings);

        // Construct the guild and tournament structure
        data.insert::<GuildTournamentsContainer>(DashMap::new());

        // Construct the tournament registry (i.e the main SquireCore API)
        data.insert::<TournamentContainer>(TournamentRegistry::new());

        // Construct the confirmations map, used in the !yes/!no commands.
        let confs: DashMap<UserId, Box<dyn Confirmation>> = DashMap::new();
        data.insert::<ConfirmationsContainer>(confs);

        // Construct the misfortunes map, used with !misfortune
        let mis_players: DashMap<UserId, RoundId> = DashMap::new();
        let misfortunes: DashMap<RoundId, Misfortune> = DashMap::new();
        data.insert::<MisfortuneContainer>(misfortunes);
        data.insert::<MisfortunePlayerContainer>(mis_players);
    }

    if let Err(why) = client.start().await {
        println!("Client error: {:?}", why);
    }
}
