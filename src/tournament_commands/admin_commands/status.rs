use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("status")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[description("Creates an auto-updating status containing all information about the tournament.")]
async fn status(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}
