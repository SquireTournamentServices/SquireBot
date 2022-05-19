use super::{
    add_deck::*, confirm_result::*, create_match::*, cut::*, decklist::*, drop::*, end::*,
    freeze::*, give_bye::*, match_result::*, match_status::*, players::*, profile::*,
    prune::PRUNE_COMMAND, raw_standings::*, register::*, registration::*, remove_deck::*,
    remove_match::*, start::*, status::*, time_extension::*,
};

use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

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
    match_status,
    players,
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
    msg.reply(
        &ctx.http,
        "Please specify a subcommand in order to adjust settings.",
    )
    .await?;
    Ok(())
}
