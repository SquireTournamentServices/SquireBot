use std::fmt::format;

use crate::model::containers::{GuildAndTournamentIDMapContainer, GuildSettingsMapContainer, TournamentMapContainer, TournamentNameAndIDMapContainer};

use super::admin_commands::admin::*;
use super::player_commands::{
    add_deck::*, confirm_result::*, decklist::*, decks::*, drop::*, list::*, match_result::*,
    name::*, ready::*, register::*, remove_deck::*, standings::*,
};
use super::settings_commands::*;

use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;
use squire_core::tournament::TournamentPreset;

/*
*/

#[command("tournament")]
#[only_in(guild)]
#[aliases("tourn", "T")]
#[sub_commands(
    admin,
    create,
    settings,
    add_deck,
    confirm_result,
    decklist,
    decks,
    drop,
    list,
    match_result,
    name,
    ready,
    register,
    remove_deck,
    standings
)]
#[description("Commands pretaining to tournaments.")]
async fn tournament(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    msg.reply(
        &ctx.http,
        "Please specify a subcommand, so I know what to do. If you're unsure, use `!help tournament`.",
    )
        .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[description("Adjust the settings of a specfic tournament.")]
async fn create(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    // Verify that the arguements are parsable and correct
    let preset = match args.single::<String>().unwrap().as_str() {
        "fluid" => TournamentPreset::Fluid,
        "swiss" => TournamentPreset::Swiss,
        _ => {
            msg.reply(
                &ctx.http,
                "Invalid tournament preset. The valid options are `fluid` and `swiss`.",
            )
                .await?;
            return Ok(());
        }
    };
    let name = args.rest().trim().to_string();
    if name.len() == 0 {
        msg.reply(
            &ctx.http,
            "Please include a name for the tournament.",
        )
            .await?;
        return Ok(());
    }
    // Get the settings data
    let data = ctx.data.read().await;
    let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
    let guild: Guild = msg.guild(&ctx.cache).unwrap();
    let settings = all_settings.get_mut(&guild.id).unwrap();
    // Ensure that tournaments can be ran
    if !settings.is_configured() {
        msg.reply(
            &ctx.http, "Error: This server isn't configured to run tournaments. Use the `!setup` command to help you with this.",
        )
            .await?;
        return Ok(());
    }
    // Create the role that the tournament will be using
    let tourn_role = match guild.create_role(&ctx.http, |r| r.mentionable(true).name(format!("{name} Player"))).await {
        Ok(role) => role,
        Err(_) => {
            msg.reply(
                &ctx.http,
                "Error: Unable to create a role for the tournament.",
            )
                .await?;
            return Ok(());
        }
    };
    // Create the tournament and store its data in the required places.
    // NOTE: `create_tournament` will only return an error if the server is not configured. We
    // already checked this, so we're safe to unwrap it.
    let tourn = settings.create_tournament(tourn_role.id, preset, name.clone()).unwrap();
    let tourn_id = tourn.tourn.id.clone();
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    all_tourns.insert(tourn_id.clone(), tourn);
    let mut name_and_id = data.get::<TournamentNameAndIDMapContainer>().unwrap().write().await;
    name_and_id.insert(name, tourn_id);
    let mut id_map = data.get::<GuildAndTournamentIDMapContainer>().unwrap().write().await;
    id_map.insert_left(tourn_id, &guild.id);
    Ok(())
}

#[command]
#[only_in(guild)]
#[sub_commands(general, pairings, scoring, discord, view)]
#[allowed_roles("Tournament Admin")]
#[description("Adjust the settings of a specfic tournament.")]
async fn settings(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    msg.reply(
        &ctx.http,
        "Please specify a subcommand in order to adjust settings.",
    )
        .await?;
    Ok(())
}
