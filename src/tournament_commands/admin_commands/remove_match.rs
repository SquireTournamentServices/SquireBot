use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("remove-match")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[description("Adds a match from the tournament.")]
async fn remove_match(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

