use super::{
    add_deck::*, confirm_result::*, create_match::*, cut::*, decklist::*, drop::*, end::*,
    freeze::*, give_bye::*, match_result::MATCH_RESULT_COMMAND, players::*, profile::*,
    prune::PRUNE_COMMAND, raw_standings::*, register::*, registration::*, remove_deck::*,
    remove_match::*, start::*, status::*, time_extension::*, pair::*
};

use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

#[command]
#[only_in(guild)]
#[sub_commands(
    add_deck,
    confirm_result,
    create_match,
    cut,
    decklist,
    drop,
    end,
    freeze,
    give_bye,
    match_result,
    players,
    pair,
    profile,
    prune,
    raw_standings,
    register,
    registration,
    remove_deck,
    remove_match,
    start,
    status,
    time_extension
)]
#[allowed_roles("Tournament Admin")]
#[description("Adjust the settings of a specfic tournament.")]
async fn admin(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    msg.reply(&ctx.http, "Please specify a subcommand.").await?;
    Ok(())
}
