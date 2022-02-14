use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("decklist")]
#[description("Prints out one of your decklists.")]
async fn decklist(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

