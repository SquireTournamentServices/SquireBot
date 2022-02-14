use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("match-result")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[description("Records the result of a match.")]
async fn match_result(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

