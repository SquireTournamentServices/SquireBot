use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("cut")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[description("Drops all but the top N players.")]
async fn cut(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

