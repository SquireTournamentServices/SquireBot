use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("decklist")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[description("Prints out the decklist of a player.")]
async fn decklist(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

