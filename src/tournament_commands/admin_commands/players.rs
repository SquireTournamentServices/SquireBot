use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("players")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[description("Prints out a list of all players.")]
async fn players(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

