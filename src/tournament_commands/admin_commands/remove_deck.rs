use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("remove-deck")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[description("Removes a deck on behave of a player.")]
async fn remove_deck(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}
