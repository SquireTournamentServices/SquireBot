use super::super::utils::is_configured;

use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("setup")]
#[sub_commands(setup_check)]
#[required_permissions("ADMINISTRATOR")]
#[description("Sets up the server to be able to run tournaments.")]
async fn setup(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[aliases("check")]
#[required_permissions("ADMINISTRATOR")]
#[description("Sets up the server to be able to run tournaments.")]
async fn setup_check(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}
