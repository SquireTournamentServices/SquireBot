use crate::model::consts::*;

use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[min_args(1)]
#[delimiters(",")]
#[description(
    "Adjusts the default settings for future tournament that don't pretain to pairings or scoring."
)]
async fn general(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[min_args(1)]
#[delimiters(",")]
#[description("Adjusts the default settings for future tournament that pretain to pairings.")]
async fn pairings(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[min_args(1)]
#[delimiters(",")]
#[description("Adjusts the default settings for future tournament that pretain to scoring.")]
async fn scoring(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}
