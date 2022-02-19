use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("decks")]
#[only_in(guild)]
#[description("Prints out a summary of your decks.")]
async fn decks(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}
