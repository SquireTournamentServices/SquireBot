use crate::model::guild_settings::{
    GuildSettings, GuildSettingsContainer, DEFAULT_JUDGE_ROLE_NAME, DEFAULT_MATCHES_CATEGORY_NAME,
    DEFAULT_PAIRINGS_CHANNEL_NAME, DEFAULT_TOURN_ADMIN_ROLE_NAME,
};
use crate::utils::is_configured;

use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("setup")]
#[sub_commands(check, test, defaults)]
#[only_in(guild)]
#[required_permissions("ADMINISTRATOR")]
#[description("Sets up the server to be able to run tournaments.")]
async fn setup(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let all_settings = data.get::<GuildSettingsContainer>().unwrap();
    let guild: Guild = msg.guild(&ctx.cache).unwrap();
    // Gets a copy of the setting. We don't want to a reference to the copy since creating what
    // needs to be created will trigger the hooks and update the shared settings object.
    let settings: GuildSettings = match all_settings.get_mut(&guild.id) {
        Some(s) => s.clone(),
        None => {
            // This case should never happen... but just in case
            all_settings.insert(guild.id.clone(), GuildSettings::from_existing(&guild));
            all_settings.get_mut(&guild.id).unwrap().clone()
        }
    };
    drop(all_settings);

    match settings.judge_role {
        Some(_) => {}
        None => {
            let _ = guild
                .create_role(&ctx.http, |r| r.name(DEFAULT_JUDGE_ROLE_NAME))
                .await?;
        }
    };
    match settings.tourn_admin_role {
        Some(_) => {}
        None => {
            let _ = guild
                .create_role(&ctx.http, |r| r.name(DEFAULT_TOURN_ADMIN_ROLE_NAME))
                .await?;
        }
    };
    match settings.pairings_channel {
        Some(_) => {}
        None => {
            let _ = guild
                .create_channel(&ctx.http, |r| {
                    r.name(DEFAULT_PAIRINGS_CHANNEL_NAME)
                        .kind(ChannelType::Text)
                })
                .await?;
        }
    };
    match settings.matches_category {
        Some(_) => {}
        None => {
            let _ = guild
                .create_channel(&ctx.http, |r| {
                    r.name(DEFAULT_MATCHES_CATEGORY_NAME)
                        .kind(ChannelType::Category)
                })
                .await?;
        }
    };

    msg.reply(
        &ctx.http,
        "The server should now be setup to run tournament. To test this, run `!setup test`.",
    )
    .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[required_permissions("ADMINISTRATOR")]
#[description("Prints out the current tournament-related settings.")]
async fn check(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[required_permissions("ADMINISTRATOR")]
#[description("Tests the setup of the server.")]
async fn test(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[required_permissions("ADMINISTRATOR")]
#[description("Changes the default settings for new tournament in the server.")]
async fn defaults(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}
