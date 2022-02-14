use super::settings_commands::*;
use super::admin_commands::{
    add_deck::*,
    confirm_result::*,
    create_match::*,
    cut::*,
    decklist::*,
    drop::*,
    end::*,
    freeze::*,
    give_bye::*,
    match_result::*,
    match_status::*,
    players::*,
    profile::*,
    prune::PRUNE_COMMAND,
    raw_standings::*,
    register::*,
    registration::*,
    remove_deck::*,
    remove_match::*,
    start::*,
    status::*,
    time_extension::*,
};

use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("tournament")]
#[only_in(guild)]
#[aliases("tourn", "T")]
#[sub_commands(admin, create, settings)]
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
async fn create(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

/*

*/
#[command]
#[only_in(guild)]
#[sub_commands(add_deck, confirm_result, create_match, cut, decklist, drop, end, freeze, give_bye, match_result, match_status, players, profile, prune, raw_standings, register, registration, remove_deck, remove_match, start, status, time_extension)]
#[allowed_roles("Tournament Admin")]
#[description("Adjust the settings of a specfic tournament.")]
async fn admin(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[sub_commands(general, pairings, scoring, discord, view)]
#[allowed_roles("Tournament Admin")]
#[description("Adjust the settings of a specfic tournament.")]
async fn settings(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    msg.reply(
        &ctx.http,
        "Please specify a subcommand, so I know what to do. If you're unsure, use `!help tournament settings`.",
    )
        .await?;
    Ok(())
}
