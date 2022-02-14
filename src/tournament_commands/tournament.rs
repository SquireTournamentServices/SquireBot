use super::settings_commands::*;
use super::admin_commands::admin::*;
use super::player_commands::{
    add_deck::*,
    confirm_result::*,
    decklist::*,
    decks::*,
    drop::*,
    list::*,
    match_result::*,
    name::*,
    ready::*,
    register::*,
    remove_deck::*,
    standings::*,
};

use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

/*
*/

#[command("tournament")]
#[only_in(guild)]
#[aliases("tourn", "T")]
#[sub_commands(admin, create, settings, add_deck, confirm_result, decklist, decks, drop, list, match_result, name, ready, register, remove_deck, standings)]
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
