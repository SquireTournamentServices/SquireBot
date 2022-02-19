use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("create-match")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[description("Adds a match consisting of the specified players.")]
async fn create_match(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}
