use crate::model::misfortune::*;

use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("misfortune")]
#[min_args(1)]
#[max_args(2)]
#[description("Helps you resolve Wheel of Misfortune.")]
async fn misfortune(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let mis = data.get::<MisfortuneContainer>();
    Ok(())
}

#[command("create")]
#[only_in(guild)]
#[min_args(0)]
#[max_args(1)]
#[description("Start resolving Wheel of Misfortune.")]
async fn create(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}
