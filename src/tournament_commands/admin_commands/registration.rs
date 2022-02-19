use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("registration")]
#[only_in(guild)]
#[aliases("reg")]
#[allowed_roles("Tournament Admin")]
#[description("Changes the registeration status of the tournament.")]
async fn registration(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}
