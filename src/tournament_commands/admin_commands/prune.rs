use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("prune")]
#[only_in(guild)]
#[sub_commands(players, decks)]
#[allowed_roles("Tournament Admin")]
#[description(
    "Removes players that aren't fully registered and decks from players that have them in excess."
)]
async fn prune(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

#[command("players")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[description("Removes players that aren't fully registered.")]
async fn players(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

#[command("decks")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[description("Removes decks from players that have them in excess.")]
async fn decks(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}
