#![allow(unused_imports, unused_variables)]

mod admin_commands;
mod judge_commands;
mod models;
mod player_commands;
mod utils;

use admin_commands::{group::ADMINCOMMANDS_GROUP, setup::*};
use models::guild_settings::{GuildSettings, GuildSettingsContainer};

use std::{
    collections::{HashMap, HashSet},
    fmt::Write,
    fs::read_to_string,
    sync::{Arc, RwLock},
};

use serenity::prelude::*;
use serenity::{
    async_trait,
    client::bridge::gateway::{GatewayIntents, ShardId, ShardManager},
    framework::standard::{
        buckets::{LimitedFor, RevertBucket},
        help_commands,
        macros::{check, command, group, help, hook},
        Args, CommandGroup, CommandOptions, CommandResult, Delimiter, DispatchError, HelpOptions,
        Reason, StandardFramework,
    },
    http::Http,
    model::{
        guild::{Guild, Role},
        channel::{GuildChannel, ChannelCategory, Channel, Embed, EmbedField, Message},
        gateway::Ready,
        id::{GuildId, UserId, RoleId},
        permissions::Permissions,
    },
    utils::{content_safe, Colour, ContentSafeOptions},
};

use dashmap::DashMap;
use dotenv::vars;
use serde_json;
use tokio::sync::Mutex;

struct Handler;

#[async_trait]
impl EventHandler for Handler {
    async fn ready(&self, _: Context, ready: Ready) {
        println!("{} is connected!", ready.user.name);
    }

    async fn guild_create(&self, _: Context, guild: Guild, _:bool) {
        todo!()
    }

    async fn category_delete(&self, _: Context, category: &ChannelCategory) {
        todo!()
    }

    async fn channel_delete(&self, _: Context, new: &GuildChannel) {
        todo!()
    }

    async fn channel_update(&self, _: Context, _: Option<Channel>, new: Channel) {
        todo!()
    }

    async fn guild_role_update(&self, _: Context, guild_id: GuildId, _: Option<Role>, new: Role) {
        todo!()
    }

    async fn guild_role_delete(&self, _: Context, guild_id: GuildId, removed_role: RoleId, _: Option<Role>) {
        todo!()
    }
}

// The framework provides two built-in help commands for you to use.
// But you can also make your own customized help command that forwards
// to the behaviour of either of them.
#[help]
// This replaces the information that a user can pass
// a command-name as argument to gain specific information about it.
#[individual_command_tip = "Hello! こんにちは！Hola! Bonjour! 您好! 안녕하세요~\n\n\
If you want more information about a specific command, just pass the command as argument."]
// Some arguments require a `{}` in order to replace it with contextual information.
// In this case our `{}` refers to a command's name.
#[command_not_found_text = "Could not find: `{}`."]
// When you use sub-groups, Serenity will use the `indention_prefix` to indicate
// how deeply an item is indented.
// The default value is "-", it will be changed to "+".
#[indention_prefix = "+"]
// On another note, you can set up the help-menu-filter-behaviour.
// Here are all possible settings shown on all possible options.
// First case is if a user lacks permissions for a command, we can hide the command.
#[lacking_permissions = "Hide"]
// If the user is nothing but lacking a certain role, we just display it hence our variant is `Nothing`.
#[lacking_role = "Nothing"]
// The last `enum`-variant is `Strike`, which ~~strikes~~ a command.
#[wrong_channel = "Strike"]
// Serenity will automatically analyse and generate a hint/tip explaining the possible
// cases of ~~strikethrough-commands~~, but only if
// `strikethrough_commands_tip_in_{dm, guild}` aren't specified.
// If you pass in a value, it will be displayed instead.
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
    match msg.reply(&ctx.http, "Look, a new command!").await {
        Ok(_) => true,
        Err(_) => false,
    }
}

#[hook]
async fn after_command(_ctx: &Context, _msg: &Message, command_name: &str, command_result: CommandResult) {
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
                // In this case, if "," would be first, a message would never
                // be delimited at ", ", forcing you to trim your arguments if you
                // want to avoid whitespaces at the start of each.
                .delimiters(vec![", ", ","])
                // Sets the bot's owners. These will be used for commands that
                // are owners only.
                .owners(owners)
        })
    // Set a function to be called prior to each command execution. This
    // provides the context of the command, the message that was received,
    // and the full name of the command that will be called.
    //
    // Avoid using this to determine whether a specific command should be
    // executed. Instead, prefer using the `#[check]` macro which
    // gives you this functionality.
    //
    // **Note**: Async closures are unstable, you may use them in your
    // application if you are fine using nightly Rust.
    // If not, we need to provide the function identifiers to the
    // hook-functions (before, after, normal, ...).
    .before(before_command)
        // Similar to `before`, except will be called directly _after_
        // command execution.
        .after(after_command)
        // The `#[group]` macro generates `static` instances of the options set for the group.
        // They're made in the pattern: `#name_GROUP` for the group instance and `#name_GROUP_OPTIONS`.
        // #name is turned all uppercase
        .help(&MY_HELP)
        .group(&ADMINCOMMANDS_GROUP);

    let mut client = Client::builder(&token)
        .event_handler(Handler)
        .framework(framework)
        // For this example to run properly, the "Presence Intent" and "Server Members Intent"
        // options need to be enabled.
        // These are needed so the `required_permissions` macro works on the commands that need to
        // use it.
        // You will need to enable these 2 options on the bot application, and possibly wait up to 5
        // minutes.
        .intents(GatewayIntents::all())
        .await
        .expect("Err creating client");

    {
        let mut data = client.data.write().await;
        let all_guild_settings: DashMap<GuildId, GuildSettings> = serde_json::from_str(
            &mut read_to_string("./guild_settings.json").expect("Guilds settings file not found."),
        )
            .expect("The guild settings data is malformed.");
        data.insert::<GuildSettingsContainer>(all_guild_settings);
    }

    if let Err(why) = client.start().await {
        println!("Client error: {:?}", why);
    }
}
