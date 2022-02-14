use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("name")]
#[only_in(guild)]
#[description("Adjust your name in the tournament.")]
async fn name(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

