use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("add-deck")]
#[description("Submits a deck.")]
async fn add_deck(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

