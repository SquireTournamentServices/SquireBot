use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("register")]
#[only_in(guild)]
#[description("Register for a tournament.")]
async fn register(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}
