use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command]
#[only_in(guild)]
#[allowed_roles(DEFAULT_TOURN_ADMIN_ROLE_NAME)]
#[description("Adjust the settings of a specfic tournament.")]
async fn general(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles(DEFAULT_TOURN_ADMIN_ROLE_NAME)]
#[description("Adjust the settings of a specfic tournament.")]
async fn pairings(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles(DEFAULT_TOURN_ADMIN_ROLE_NAME)]
#[description("Adjust the settings of a specfic tournament.")]
async fn scoring(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

