use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("register")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[description("Registers a player on their behalf.")]
async fn register(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}
