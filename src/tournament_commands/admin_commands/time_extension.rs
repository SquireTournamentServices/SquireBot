use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("time-extension")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[description("Give a match a time extenstion.")]
async fn time_extension(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

