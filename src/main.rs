//#![deny(unused)]
//#![feature(result_flattening)]

use std::{
    collections::{HashMap, HashSet},
    fs::{read_to_string, File},
    io::Write,
    path::Path,
    sync::Arc,
    thread, time,
};

use chrono::{Duration, NaiveTime, Utc};
use logging::LogAction;
use serenity::{
    async_trait,
    builder::CreateApplicationCommand,
    framework::standard::{
        help_commands,
        macros::{help, hook},
        Args, CommandGroup, CommandResult, HelpOptions, StandardFramework,
    },
    http::Http,
    model::{
        channel::{Channel, ChannelCategory, ChannelType, GuildChannel, Message},
        gateway::GatewayIntents,
        gateway::Ready,
        guild::{Guild, Member, Role},
        id::{GuildId, RoleId, UserId},
        prelude::{
            command::{Command, CommandOptionType},
            interaction::{Interaction, InteractionResponseType},
        },
        user::User,
    },
    prelude::*,
};

use dashmap::DashMap;
use tokio::{sync::mpsc::unbounded_channel, time::Instant};

use mtgjson::mtgjson::meta::Meta;
use squire_lib::{
    self,
    operations::{PlayerOp, TournOp},
    tournament::TournamentId,
};

mod env;
mod logging;
mod match_manager;
mod misc_commands;
mod model;
mod setup_commands;
mod tournament_commands;
mod utils;

use crate::{
    env::*,
    logging::LogTracker,
    match_manager::MatchManager,
    misc_commands::group::MISCCOMMANDS_GROUP,
    model::{
        confirmation::Confirmation,
        consts::*,
        containers::*,
        guilds::{GuildTournRegistry, GuildTournament},
    },
    setup_commands::setup::SETUPCOMMANDS_GROUP,
    tournament_commands::tournament::TOURNAMENTCOMMANDS_GROUP,
    utils::{card_collection::build_collection, spin_lock::spin_mut},
};

pub fn register_sub_command(
    command: &mut CreateApplicationCommand,
) -> &mut CreateApplicationCommand {
    command
        .name("subcommand")
        .description("Test subcommand")
        .create_option(|option| option)
}

pub fn register_base_command(
    command: &mut CreateApplicationCommand,
) -> &mut CreateApplicationCommand {
    command
        .name("base-command")
        .description("Test base command")
        .create_option(|option| {
            option
                .name("subcommand-a")
                .description("A subcommand")
                .kind(CommandOptionType::SubCommandGroup)
        })
}

struct Handler;

#[async_trait]
impl EventHandler for Handler {
    async fn ready(&self, ctx: Context, _ready: Ready) {
        println!("SquireBot is ready!!");
        Command::create_global_application_command(&ctx.http, |command| {
            register_base_command(command)
        })
        .await
        .unwrap();
    }

    async fn interaction_create(&self, ctx: Context, interaction: Interaction) {
        if let Interaction::ApplicationCommand(command) = interaction {
            println!("{}", command.application_id);

            if let Err(why) = command
                .create_interaction_response(&ctx.http, |response| {
                    response
                        .kind(InteractionResponseType::ChannelMessageWithSource)
                        .interaction_response_data(|message| message.content("Testing..."))
                })
                .await
            {
                println!("Cannot respond to slash command: {}", why);
            }
        }
    }

    async fn guild_create(&self, ctx: Context, guild: Guild, _: bool) {
        let data = ctx.data.read().await;
        let tourn_regs = data
            .get::<GuildTournRegistryMapContainer>()
            .unwrap()
            .read()
            .await;
        match spin_mut(&tourn_regs, &guild.id).await {
            Some(mut reg) => {
                reg.settings.update(&guild);
            }
            None => {
                let reg = GuildTournRegistry::new(guild.id);
                tourn_regs.insert(guild.id, reg);
            }
        };
    }

    async fn category_create(&self, ctx: Context, new: &ChannelCategory) {
        let data = ctx.data.read().await;
        let tourn_regs = data
            .get::<GuildTournRegistryMapContainer>()
            .unwrap()
            .read()
            .await;
        if let Some(mut reg) = spin_mut(&tourn_regs, &new.guild_id).await {
            if reg.settings.matches_category.is_none() && new.name == DEFAULT_MATCHES_CATEGORY_NAME
            {
                reg.settings.matches_category = Some(new.clone());
            }
        };
    }

    async fn category_delete(&self, ctx: Context, category: &ChannelCategory) {
        let data = ctx.data.read().await;
        let tourn_regs = data
            .get::<GuildTournRegistryMapContainer>()
            .unwrap()
            .read()
            .await;
        if let Some(mut reg) = spin_mut(&tourn_regs, &category.guild_id).await {
            match &reg.settings.matches_category {
                Some(c) if c.id == category.id => {
                    reg.settings.matches_category = None;
                }
                _ => {}
            }
        };
    }

    async fn channel_create(&self, ctx: Context, new: &GuildChannel) {
        let data = ctx.data.read().await;
        let tourn_regs = data
            .get::<GuildTournRegistryMapContainer>()
            .unwrap()
            .read()
            .await;
        if let Some(mut reg) = spin_mut(&tourn_regs, &new.guild_id).await {
            if reg.settings.pairings_channel.is_none() && new.name == DEFAULT_PAIRINGS_CHANNEL_NAME
            {
                reg.settings.pairings_channel = Some(new.clone());
            }
        };
    }

    async fn channel_delete(&self, ctx: Context, channel: &GuildChannel) {
        let data = ctx.data.read().await;
        let tourn_regs = data
            .get::<GuildTournRegistryMapContainer>()
            .unwrap()
            .read()
            .await;
        if let Some(mut reg) = spin_mut(&tourn_regs, &channel.guild_id).await {
            match &reg.settings.pairings_channel {
                Some(c) if c.id == channel.id => {
                    reg.settings.pairings_channel = None;
                }
                _ => {}
            }
        };
    }

    // NOTE: This covers both categories and guild channels
    async fn channel_update(&self, ctx: Context, _: Option<Channel>, new: Channel) {
        let data = ctx.data.read().await;
        let tourn_regs = data
            .get::<GuildTournRegistryMapContainer>()
            .unwrap()
            .read()
            .await;
        match new {
            Channel::Guild(c)
                if c.kind == ChannelType::Text && c.name == DEFAULT_PAIRINGS_CHANNEL_NAME =>
            {
                if let Some(mut reg) = spin_mut(&tourn_regs, &c.guild_id).await {
                    if reg.settings.pairings_channel.is_none() {
                        reg.settings.pairings_channel = Some(c.clone());
                    }
                }
            }
            Channel::Category(c) if c.name == DEFAULT_MATCHES_CATEGORY_NAME => {
                if let Some(mut reg) = spin_mut(&tourn_regs, &c.guild_id).await {
                    if reg.settings.matches_category.is_none() {
                        reg.settings.matches_category = Some(c.clone());
                    }
                }
            }
            _ => {}
        };
    }

    async fn guild_role_create(&self, ctx: Context, new: Role) {
        let data = ctx.data.read().await;
        let tourn_regs = data
            .get::<GuildTournRegistryMapContainer>()
            .unwrap()
            .read()
            .await;
        let mut reg = spin_mut(&tourn_regs, &new.guild_id).await.unwrap();
        match new.name.as_str() {
            DEFAULT_JUDGE_ROLE_NAME if reg.settings.judge_role.is_none() => {
                reg.settings.judge_role = Some(new.id);
            }
            DEFAULT_TOURN_ADMIN_ROLE_NAME if reg.settings.tourn_admin_role.is_none() => {
                reg.settings.tourn_admin_role = Some(new.id);
            }
            _ => {}
        };
    }

    async fn guild_role_update(&self, ctx: Context, _: Option<Role>, new: Role) {
        let data = ctx.data.read().await;
        let tourn_regs = data
            .get::<GuildTournRegistryMapContainer>()
            .unwrap()
            .read()
            .await;
        let mut reg = spin_mut(&tourn_regs, &new.guild_id).await.unwrap();
        match new.name.as_str() {
            DEFAULT_JUDGE_ROLE_NAME if reg.settings.judge_role.is_none() => {
                reg.settings.judge_role = Some(new.id);
            }
            DEFAULT_TOURN_ADMIN_ROLE_NAME if reg.settings.tourn_admin_role.is_none() => {
                reg.settings.tourn_admin_role = Some(new.id);
            }
            _ => {
                // Makes sure that the tournament admin and judge roles aren't renamed.
                if let Some(id) = reg.settings.judge_role {
                    if new.id == id {
                        reg.settings.judge_role = None;
                    }
                }
                if let Some(id) = reg.settings.tourn_admin_role {
                    if new.id == id {
                        reg.settings.tourn_admin_role = None;
                    }
                }
            }
        }
    }

    async fn guild_role_delete(
        &self,
        ctx: Context,
        guild_id: GuildId,
        removed_role: RoleId,
        _: Option<Role>,
    ) {
        let data = ctx.data.read().await;
        let tourn_regs = data
            .get::<GuildTournRegistryMapContainer>()
            .unwrap()
            .read()
            .await;
        let mut reg = spin_mut(&tourn_regs, &guild_id).await.unwrap();
        if let Some(id) = reg.settings.judge_role {
            if id == removed_role {
                reg.settings.judge_role = Some(id);
            }
        } else if let Some(id) = reg.settings.tourn_admin_role {
            if id == removed_role {
                reg.settings.tourn_admin_role = Some(id);
            }
        }
    }

    async fn guild_member_removal(
        &self,
        ctx: Context,
        guild_id: GuildId,
        user: User,
        _: Option<Member>,
    ) {
        let data = ctx.data.read().await;
        let tourn_regs = data
            .get::<GuildTournRegistryMapContainer>()
            .unwrap()
            .read()
            .await;
        let mut reg = spin_mut(&tourn_regs, &guild_id).await.unwrap();
        for tourn in reg.tourns.values_mut() {
            if let Some(plyr_id) = tourn.get_player_id(&user.id) {
                let _ = tourn
                    .tourn
                    .apply_op(TournOp::PlayerOp(plyr_id, PlayerOp::DropPlayer));
            }
        }
    }
}

// The framework provides two built-in help commands for you to use.
// But you can also make your own customized help command that forwards
// to the behaviour of either of them.
#[help("sb-help")]
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
async fn before_command(ctx: &Context, msg: &Message, command_name: &str) -> bool {
    let _ = ctx
        .data
        .read()
        .await
        .get::<LogActionSenderContainer>()
        .unwrap()
        .send((msg.id, LogAction::Start(msg.content.clone(), Utc::now())));
    println!("Processing command: {command_name}");
    true
}

#[hook]
async fn after_command(
    ctx: &Context,
    msg: &Message,
    command_name: &str,
    command_result: CommandResult,
) {
    let data = ctx.data.read().await;
    let sender = data.get::<LogActionSenderContainer>().unwrap();
    match command_result {
        Ok(()) => {
            let _ = sender.send((msg.id, LogAction::End(true, Utc::now())));
            println!("Success on command: {command_name}");
        }
        Err(why) => {
            let _ = sender.send((msg.id, LogAction::End(false, Utc::now())));
            println!("Error on command: {command_name} with error {:?}", why);
        }
    }
}

#[tokio::main]
async fn main() {
    // Configure the client with your Discord bot token in the environment.
    let env_vars: HashMap<String, String> = dotenv::vars().collect();
    let token = env_vars
        .get(TOKEN)
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

    let (sender, receiver) = unbounded_channel();

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

    let intents = GatewayIntents::GUILDS
        .union(GatewayIntents::DIRECT_MESSAGES)
        .union(GatewayIntents::MESSAGE_CONTENT)
        .union(GatewayIntents::GUILD_MESSAGES);

    let mut client = Client::builder(token, intents)
        .event_handler(Handler)
        .framework(framework)
        .await
        .expect("Err creating client");

    {
        let mut data = client.data.write().await;

        data.insert::<LogActionSenderContainer>(Arc::new(sender));

        /*
        let db_uri = env_vars
            .get(MONGO_DB_URL)
            .expect("Env file does not contain a `MONGO_DB_URL`");
        let client = mongodb::Client::with_uri_str(db_uri).await.expect("Could not connect to mongodb");
        let tourns = client.database("Tournaments");
        let settings = client.database("Settings");

        let live_tourn_coll = tourns.collection::<GuildTournament>("Live Tournaments");
        let dead_tourn_coll = tourns.collection::<GuildTournament>("Dead Tournaments");
        let guild_settings_coll = settings.collection::<GuildSettings>("Guild Settings");

        data.insert::<TournamentCollectionContainer>(Arc::new(live_tourn_coll.clone()));
        data.insert::<DeadTournamentCollectionContainer>(Arc::new(dead_tourn_coll.clone()));
        data.insert::<SettingsCollectionContainer>(Arc::new(guild_settings_coll.clone()));
        */

        // Construct the main TournamentID -> Tournament map
        let tourn_regs: DashMap<GuildId, GuildTournRegistry> = serde_json::from_str(
            &read_to_string("./tournaments.json").expect("Tournament file could not be found."),
        )
        .expect("The tournament data is malformed.");

        let (match_send, match_rec) = unbounded_channel();
        data.insert::<MatchUpdateSenderContainer>(Arc::new(match_send));
        let mut match_manager = MatchManager::new(match_rec);
        for reg in tourn_regs.iter() {
            for tourn in reg.tourns.values() {
                for tr in tourn
                    .guild_rounds
                    .keys()
                    .filter_map(|r| tourn.get_tracking_round(r))
                {
                    match_manager.add_match(tr);
                }
            }
        }

        let tourn_regs = RwLock::new(tourn_regs);

        // Insert the main TournamentID -> Tournament map
        let ref_main = Arc::new(tourn_regs);
        let tourns_ref = ref_main.clone();
        let cache_ref = client.cache_and_http.clone();
        data.insert::<GuildTournRegistryMapContainer>(ref_main);

        // Match embed and timer notification updater
        tokio::spawn(async move {
            let cache = cache_ref;
            let loop_length = time::Duration::from_secs(30);
            loop {
                let timer = Instant::now();
                match_manager.update_matches(&cache).await;
                if timer.elapsed() < loop_length {
                    let mut sleep = tokio::time::interval(loop_length - timer.elapsed());
                    sleep.tick().await;
                    sleep.tick().await;
                }
            }
        });

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
            let mut meta = meta;
            let cards = other_card_ref;
            let path = Path::new("./AtomicCards.json");
            let mut interval = tokio::time::interval(time::Duration::from_secs(1800));
            interval.tick().await;
            loop {
                if let Some((m, coll)) = build_collection(&meta, path).await {
                    let mut card_lock = cards.write().await;
                    meta = m;
                    *card_lock = coll;
                }
                interval.tick().await;
            }
        });
        data.insert::<CardCollectionContainer>(card_ref);

        let dead_tournaments: HashMap<TournamentId, GuildTournament> =
            read_to_string("./dead_tournaments.json")
                .map(|data| {
                    serde_json::from_str(data.as_str()).expect("Malformed dead tournament data")
                })
                .unwrap_or_default();
        let dead_tourns = Arc::new(RwLock::new(dead_tournaments));
        let dead_tourns_ref = dead_tourns.clone();
        data.insert::<DeadTournamentMapContainer>(dead_tourns);

        // Spawns an await task to save all data every 15 minutes
        tokio::spawn(async move {
            let tourns = tourns_ref;
            let dead_tourns = dead_tourns_ref;
            let mut interval = tokio::time::interval(time::Duration::from_secs(900));
            loop {
                interval.tick().await;
                let tourns_lock = tourns.write().await;
                if let Ok(data) = serde_json::to_string(&*tourns_lock) {
                    if let Ok(mut file) = File::create("tournaments.json") {
                        let _ = write!(file, "{data}");
                    }
                }
                let dead_tourns_lock = dead_tourns.write().await;
                if let Ok(data) = serde_json::to_string(&*dead_tourns_lock) {
                    if let Ok(mut file) = File::create("dead_tournaments.json") {
                        let _ = write!(file, "{data}");
                    }
                }
            }
        });
    }

    let issue_channel = match client
        .cache_and_http
        .http
        .get_channel(env_vars.get(ISSUE_CHANNEL_ID).unwrap().parse().unwrap())
        .await
        .unwrap()
    {
        Channel::Guild(channel) => channel,
        _ => {
            eprintln!("The given issue channel id was not a guild channel. Exiting");
            return;
        }
    };
    let telemetry_channel = match client
        .cache_and_http
        .http
        .get_channel(env_vars.get(TELEMETRY_CHANNEL_ID).unwrap().parse().unwrap())
        .await
        .unwrap()
    {
        Channel::Guild(channel) => channel,
        _ => {
            eprintln!("The given telemetry channel id was not a guild channel. Exiting");
            return;
        }
    };

    let mut logger = LogTracker::new(telemetry_channel, issue_channel, receiver);
    let cache = client.cache_and_http.clone();

    // Logger
    tokio::spawn(async move {
        let loop_length = time::Duration::from_secs(5);
        let tomorrow = Utc::now().date_naive() + Duration::hours(24);
        let midnight = NaiveTime::from_hms(0, 0, 0);
        let mut report_time = tomorrow.and_time(midnight).and_local_timezone(Utc).unwrap();
        loop {
            let timer = Instant::now();
            let issues = logger.process();
            logger.report_issues(&cache, issues).await;
            if Utc::now() > report_time {
                report_time += Duration::hours(24);
                logger.report_telemetry(&cache).await;
            }
            if timer.elapsed() < loop_length {
                let mut sleep = tokio::time::interval(loop_length - timer.elapsed());
                sleep.tick().await;
                sleep.tick().await;
            }
        }
    });

    let max_retries = 10;
    let mut retry_count = 0;
    while let Err(why) = client.start().await {
        println!("Failed to start client. Reason: {:?}", why);
        retry_count += 1;
        if retry_count == max_retries {
            println!("Client start failed {max_retries} times. Aborting");
            return;
        }
        // Sleep for 16 milliseconds, then 32, then 64, and so on
        thread::sleep(time::Duration::from_millis(0b1000 << retry_count));
    }
}
