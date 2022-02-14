use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("remove-deck")]
#[only_in(guild)]
#[description("Removes one of your decks.")]
async fn remove_deck(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

