use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("freeze")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[description("Pauses a tournament.")]
async fn freeze(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

#[command("thaw")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[description("Resumes a frozen a tournament.")]
async fn thaw(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}
