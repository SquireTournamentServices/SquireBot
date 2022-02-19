use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("raw-standings")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[description("Delivers a txt file with simplified standings.")]
async fn raw_standings(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}
