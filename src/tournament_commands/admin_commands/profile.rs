use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("profile")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[description("Prints out the profile of a player.")]
async fn profile(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}
