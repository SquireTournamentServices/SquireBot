use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("give-bye")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[description("Gives a player a bye.")]
async fn give_bye(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

