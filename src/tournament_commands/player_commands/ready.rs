use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("ready")]
#[only_in(guild)]
#[aliases("lfg")]
#[description("Shows that you're ready to play your next match.")]
async fn ready(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

#[command("unready")]
#[only_in(guild)]
#[aliases("leave-lfg")]
#[description("Shows that you're not ready to play your next match.")]
async fn unready(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}
