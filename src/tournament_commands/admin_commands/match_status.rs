use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("match-status")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[description("Prints an auto-updating embed of the status of a match.")]
async fn match_status(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

