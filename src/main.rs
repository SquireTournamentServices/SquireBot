#![allow(unused_mut, unused_imports, dead_code, unused_variables)]

mod misc_commands;
mod model;
mod setup_commands;
mod tournament_commands;
mod utils;

use cycle_map::{CycleMap, GroupMap};
use mtgjson::mtgjson::meta::Meta;
use squire_core::{self, round::RoundId, tournament::TournamentId};

use misc_commands::{flip_coins::*, group::MISCCOMMANDS_GROUP};
use model::{
    confirmation::Confirmation, consts::*, containers::*, guild_settings::GuildSettings,
    misfortune::*,
};
use setup_commands::{group::SETUPCOMMANDS_GROUP, setup::*};
use tournament_commands::group::TOURNAMENTCOMMANDS_GROUP;

use utils::{
    card_collection::build_collection,
    embeds::{update_match_message, update_standings_message, update_status_message},
};

use dashmap::{rayon, DashMap};
use dotenv::vars;
use serde_json;
use serenity::{
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
    prelude::*,
};
use tokio::{sync::Mutex, time::Instant};

use std::{
    collections::{HashMap, HashSet},
    fs::{read_to_string, File},
    io::Write,
    path::Path,
    sync::Arc,
    time::Duration,
};

use crate::model::guild_tournament::GuildTournament;

struct Handler;

#[async_trait]
impl EventHandler for Handler {
    async fn ready(&self, _: Context, ready: Ready) {
        println!("{} is connected!", ready.user.name);
    }

    async fn guild_create(&self, ctx: Context, guild: Guild, _: bool) {
        println!("Look, a guild: {}", guild.name);
        let data = ctx.data.read().await;
        let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
        if let Some(mut settings) = all_settings.get_mut(&guild.id) {
            settings.update(&guild);
        } else {
            let settings = GuildSettings::from_existing(&guild);
            println!("{:#?}", settings);
            all_settings.insert(guild.id, settings);
        }
        std::fs::write(
            "guild_settings.json",
            serde_json::to_string(all_settings.as_ref())
                .expect("Failed to serialize guild settings."),
        )
        .expect("Failed to save guild settings json.");
    }

    async fn category_create(&self, ctx: Context, new: &ChannelCategory) {
        let data = ctx.data.read().await;
        let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
        if let Some(mut settings) = all_settings.get_mut(&new.guild_id) {
            match settings.matches_category {
                None => {
                    if new.name == DEFAULT_MATCHES_CATEGORY_NAME {
                        settings.matches_category = Some(new.clone());
                    }
                }
                Some(_) => {}
            }
        };
    }

    async fn category_delete(&self, ctx: Context, category: &ChannelCategory) {
        let data = ctx.data.read().await;
        let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
        if let Some(mut settings) = all_settings.get_mut(&category.guild_id) {
            match &settings.matches_category {
                Some(c) => {
                    if c.id == category.id {
                        settings.matches_category = None;
                    }
                }
                None => {}
            }
        };
    }

    async fn channel_create(&self, ctx: Context, new: &GuildChannel) {
        let data = ctx.data.read().await;
        let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
        if let Some(mut settings) = all_settings.get_mut(&new.guild_id) {
            match &settings.pairings_channel {
                None => {
                    if new.name == DEFAULT_PAIRINGS_CHANNEL_NAME {
                        settings.pairings_channel = Some(new.clone());
                    }
                }
                Some(c) => {}
            }
        };
    }

    async fn channel_delete(&self, ctx: Context, channel: &GuildChannel) {
        let data = ctx.data.read().await;
        let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
        if let Some(mut settings) = all_settings.get_mut(&channel.guild_id) {
            match &settings.pairings_channel {
                Some(c) => {
                    if c.id == channel.id {
                        settings.pairings_channel = None;
                    }
                }
                None => {}
            }
        };
    }

    // NOTE: This covers both categories and guild channels
    async fn channel_update(&self, ctx: Context, _: Option<Channel>, new: Channel) {
        let data = ctx.data.read().await;
        let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
        match new {
            Channel::Guild(c) => {
                if c.kind == ChannelType::Text && c.name == DEFAULT_PAIRINGS_CHANNEL_NAME {
                    if let Some(mut settings) = all_settings.get_mut(&c.guild_id) {
                        match &settings.pairings_channel {
                            None => {
                                settings.pairings_channel = Some(c);
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
                                settings.matches_category = Some(c);
                            }
                            Some(_) => {}
                        }
                    }
                }
            }
            _ => {}
        };
    }

    async fn guild_role_create(&self, ctx: Context, new: Role) {
        let data = ctx.data.read().await;
        let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
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
        };
    }

    async fn guild_role_update(&self, ctx: Context, _: Option<Role>, new: Role) {
        let data = ctx.data.read().await;
        let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
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
        };
    }

    async fn guild_role_delete(
        &self,
        ctx: Context,
        guild_id: GuildId,
        removed_role: RoleId,
        _: Option<Role>,
    ) {
        let data = ctx.data.read().await;
        let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
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
        };
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

    let http = Http::new(token);

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

    let intents = GatewayIntents::empty();
    let intests = intents.guilds();
    let intests = intents.direct_messages();

    let mut client = Client::builder(&token, intents)
        .event_handler(Handler)
        .framework(framework)
        //.intents(GatewayIntents::all())
        .await
        .expect("Err creating client");

    {
        let mut data = client.data.write().await;

        // Construct the default settings for a guild, stored in the json file.
        let all_guild_settings: DashMap<GuildId, GuildSettings> = serde_json::from_str(
            &read_to_string("./guild_settings.json").expect("Guilds settings file not found."),
        )
        .expect("The guild settings data is malformed.");
        let ref_main = Arc::new(all_guild_settings);
        let settings_ref = ref_main.clone();
        data.insert::<GuildSettingsMapContainer>(ref_main);

        // Construct the main TournamentID -> Tournament map
        let all_tournaments: DashMap<TournamentId, GuildTournament> = serde_json::from_str(
            &read_to_string("./tournaments.json").expect("Tournament file could not be found."),
        )
        .expect("The tournament data is malformed.");

        let tourn_name_and_id_map: CycleMap<String, TournamentId> = all_tournaments
            .iter()
            .map(|t| (t.tourn.name.clone(), t.tourn.id.clone()))
            .collect();
        let guild_and_tourn_id_map: GroupMap<TournamentId, GuildId> = all_tournaments
            .iter()
            .map(|t| (t.tourn.id.clone(), t.guild_id))
            .collect();

        // Insert the main TournamentID -> Tournament map
        let ref_main = Arc::new(all_tournaments);
        let tourns_ref = ref_main.clone();
        let ref_one = ref_main.clone();
        let cache_one = client.cache_and_http.clone();
        let ref_two = ref_main.clone();
        let cache_two = client.cache_and_http.clone();
        let ref_three = ref_main.clone();
        let cache_three = client.cache_and_http.clone();
        data.insert::<TournamentMapContainer>(ref_main);
        // Set up a the standings, match, and status embed updaters
        tokio::spawn(async move {
            let tourns = ref_one;
            let cache = cache_one;
            let loop_length = Duration::from_secs(30);
            loop {
                let timer = Instant::now();
                // TODO: This should be par_iter via rayon
                for mut pair in tourns.iter_mut() {
                    let mut tourn = pair.value_mut();
                    if !tourn.update_standings || tourn.standings_message.is_none() {
                        continue;
                    }
                    let standings = tourn.tourn.get_standings();
                    update_standings_message(
                        &cache,
                        tourn.standings_message.as_mut().unwrap(),
                        &tourn.players,
                        &tourn.tourn,
                        standings,
                    )
                    .await;
                    tourn.update_standings = false;
                }
                // Sleep so that the next loop starts 30 seconds after the start of this one
                if timer.elapsed() < loop_length {
                    let mut sleep = tokio::time::interval(loop_length - timer.elapsed());
                    sleep.tick().await;
                }
            }
        });
        // Match embed and timer notification updater
        tokio::spawn(async move {
            let tourns = ref_two;
            let cache = cache_two;
            let loop_length = Duration::from_secs(60);
            loop {
                let timer = Instant::now();
                // TODO: This should be par_iter via rayon
                for mut pair in tourns.iter_mut() {
                    let mut tourn = pair.value_mut();
                    for (id, msg) in tourn.match_timers.iter_mut() {
                        let round = tourn.tourn.get_round(id).unwrap();
                        let time_left = round.time_left().as_secs();
                        let mut warnings = tourn.round_warnings.get_mut(id).unwrap();
                        if time_left > 0 {
                            update_match_message(
                                &cache,
                                msg,
                                tourn.tourn.use_table_number,
                                tourn.match_vcs.get(id).map(|c| c.id),
                                tourn.match_tcs.get(id).map(|c| c.id),
                                &tourn.players,
                                &tourn.tourn,
                                &round,
                            )
                            .await;
                        }
                        if time_left == 0 && !warnings.time_up {
                            warnings.time_up = true;
                            let content = match tourn.match_roles.get(id) {
                                Some(role) => {
                                    format!("<@&{}>, time is up in your match.", role.id.0)
                                }
                                None => {
                                    format!(
                                        "Match {}, time is up in your match.",
                                        round.match_number
                                    )
                                }
                            };
                            let _ = tourn
                                .pairings_channel
                                .send_message(&cache, |m| m.content(content))
                                .await;
                        } else if time_left <= 60 && !warnings.one_min {
                            warnings.one_min = true;
                            let content = match tourn.match_roles.get(id) {
                                Some(role) => {
                                    format!(
                                        "<@&{}>, you have 1 minute left in your match.",
                                        role.id.0
                                    )
                                }
                                None => {
                                    format!(
                                        "Match {}, you have 1 minute left in your match.",
                                        round.match_number
                                    )
                                }
                            };
                            let _ = tourn
                                .pairings_channel
                                .send_message(&cache, |m| m.content(content))
                                .await;
                        } else if time_left <= 300 && !warnings.five_min {
                            warnings.five_min = true;
                            let content = match tourn.match_roles.get(id) {
                                Some(role) => {
                                    format!(
                                        "<@&{}>, you have 5 minutes left in your match.",
                                        role.id.0
                                    )
                                }
                                None => {
                                    format!(
                                        "Match {}, you have 5 minutes left in your match.",
                                        round.match_number
                                    )
                                }
                            };
                            let _ = tourn
                                .pairings_channel
                                .send_message(&cache, |m| m.content(content))
                                .await;
                        }
                    }
                }
                // Sleep so that the next loop starts 60 seconds after the start of this one
                if timer.elapsed() < loop_length {
                    let mut sleep = tokio::time::interval(loop_length - timer.elapsed());
                    sleep.tick().await;
                }
            }
        });
        // Tournament status updater
        tokio::spawn(async move {
            let tourns = ref_three;
            let cache = cache_three;
            let loop_length = Duration::from_secs(30);
            loop {
                let timer = Instant::now();
                // TODO: This should be par_iter via rayon
                for mut pair in tourns.iter_mut() {
                    let mut tourn = pair.value_mut();
                    if !tourn.update_status || tourn.tourn_status.is_none() {
                        continue;
                    }
                    update_status_message(&cache, tourn).await;
                    tourn.update_status = false;
                }
                // Sleep so that the next loop starts 30 seconds after the start of this one
                if timer.elapsed() < loop_length {
                    let mut sleep = tokio::time::interval(loop_length - timer.elapsed());
                    sleep.tick().await;
                }
            }
        });

        // Construct the Tournament Name <-> TournamentID cycle map
        data.insert::<TournamentNameAndIDMapContainer>(Arc::new(RwLock::new(
            tourn_name_and_id_map,
        )));

        // Construct the GuildID <-> TournamentID group map
        data.insert::<GuildAndTournamentIDMapContainer>(Arc::new(RwLock::new(
            guild_and_tourn_id_map,
        )));

        // Construct the confirmations map, used in the !yes/!no commands.
        let confs: DashMap<UserId, Box<dyn Confirmation>> = DashMap::new();
        data.insert::<ConfirmationsContainer>(Arc::new(confs));

        // Construct the card collection
        let path = Path::new("./AtomicCards.json");
        let meta = Meta {
            date: String::new(),
            version: String::new(),
        }; // Spoof the initial meta
        let (meta, cards) = build_collection(&meta, path)
            .await
            .expect("Could not build card colletion");
        let card_ref = Arc::new(RwLock::new(cards));
        let other_card_ref = card_ref.clone();
        // Spawns an await task to update the card collection every week.
        tokio::spawn(async move {
            let meta = meta;
            let cards = other_card_ref;
            let path = Path::new("./AtomicCards.json");
            let mut interval = tokio::time::interval(Duration::from_secs(1800));
            interval.tick().await;
            loop {
                if let Some((meta, coll)) = build_collection(&meta, path).await {
                    let mut card_lock = cards.write().await;
                    *card_lock = coll;
                }
                interval.tick().await;
            }
        });
        data.insert::<CardCollectionContainer>(card_ref);

        // Construct the misfortunes map, used with !misfortune
        let mis_players: GroupMap<UserId, RoundId> = GroupMap::new();
        let misfortunes: DashMap<RoundId, Misfortune> = DashMap::new();
        data.insert::<MisfortuneMapContainer>(Arc::new(misfortunes));
        data.insert::<MisfortuneUserMapContainer>(Arc::new(RwLock::new(mis_players)));

        // Spawns an await task to save all data every 15 minutes
        tokio::spawn(async move {
            let tourns = tourns_ref;
            let settings = settings_ref;
            let mut interval = tokio::time::interval(Duration::from_secs(900));
            loop {
                interval.tick().await;
                if let Ok(data) = serde_json::to_string(&*tourns) {
                    if let Ok(mut file) = File::create("tournaments.json") {
                        let _ = write!(file, "{data}");
                    }
                }
                if let Ok(data) = serde_json::to_string(&*settings) {
                    if let Ok(mut file) = File::create("guild_settings.json") {
                        let _ = write!(file, "{data}");
                    }
                }
            }
        });
    }

    if let Err(why) = client.start().await {
        println!("Client error: {:?}", why);
    }
}
