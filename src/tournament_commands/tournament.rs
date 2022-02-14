use super::settings_commands::*;

use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("tournament")]
#[aliases("tourn", "T")]
#[sub_commands(admin, create, settings)]
#[only_in(guild)]
#[description("Commands pretaining to tournaments.")]
async fn tournament(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    msg.reply(&ctx.http, "Please specify a subcommand, so I know what to do.").await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles(DEFAULT_TOURN_ADMIN_ROLE_NAME)]
#[description("Adjust the settings of a specfic tournament.")]
async fn admin(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles(DEFAULT_TOURN_ADMIN_ROLE_NAME)]
#[description("Adjust the settings of a specfic tournament.")]
async fn create(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[sub_commands(general, pairings, scoring)]
#[allowed_roles(DEFAULT_TOURN_ADMIN_ROLE_NAME)]
#[description("Adjust the settings of a specfic tournament.")]
async fn settings(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}
