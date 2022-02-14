use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("standings")]
#[only_in(guild)]
#[description("Prints out your place in the standigns and your score(s).")]
async fn standings(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

