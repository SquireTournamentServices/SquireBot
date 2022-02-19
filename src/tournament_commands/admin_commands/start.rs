use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("start")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[description("Starts a tournament.")]
async fn start(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}
