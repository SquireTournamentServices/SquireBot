use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("confirm-result")]
#[only_in(guild)]
#[description("Confirm the result of your match.")]
async fn confirm_result(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

