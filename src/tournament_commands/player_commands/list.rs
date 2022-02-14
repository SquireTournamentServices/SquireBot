use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("list")]
#[only_in(guild)]
#[description("Lists out all tournament in the server.")]
async fn list(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

