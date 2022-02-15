use crate::model::confirmations::confirmation_map::ConfirmationsContainer;

use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command]
#[help_available(false)]
#[description("Confirms your waiting request.")]
async fn yes(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

#[command]
#[help_available(false)]
#[description("Denies your waiting request.")]
async fn no(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}
