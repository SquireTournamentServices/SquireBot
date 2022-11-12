use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::Message,
    prelude::Context,
};

use crate::utils::default_response::subcommand_default;

use super::admin_commands::*;

#[command]
#[aliases("a")]
#[only_in(guild)]
#[sub_commands(
    add_deck,
    confirm_result,
    create_match,
    cut,
    decklist,
    drop,
    end,
    cancel,
    freeze,
    give_bye,
    match_result,
    match_status,
    pair,
    profile,
    prune,
    raw_standings,
    register,
    re_register,
    registration,
    remove_deck,
    remove_match,
    standings,
    start,
    status,
    time_extension,
    view_players,
    deck_check,
    deck_dump
)]
#[usage("<option>")]
#[allowed_roles("Tournament Admin")]
#[description("Adjust the settings of a specfic tournament.")]
async fn admin(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    subcommand_default(ctx, msg, "tournament admin").await
}
