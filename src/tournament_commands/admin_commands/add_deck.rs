use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("add-deck")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[description("Adds a deck on behalf of a player.")]
async fn add_deck(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

