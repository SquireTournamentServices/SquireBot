use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_core::{operations::TournOp, player_registry::PlayerIdentifier};

use crate::{
    model::containers::{
        GuildAndTournamentIDMapContainer, TournamentMapContainer, TournamentNameAndIDMapContainer,
    },
    utils::{
        error_to_reply::error_to_reply,
        tourn_resolver::{admin_tourn_id_resolver, user_id_resolver},
    },
};

#[command("create-match")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[description("Adds a match consisting of the specified players.")]
async fn create_match(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let name_and_id = data
        .get::<TournamentNameAndIDMapContainer>()
        .unwrap()
        .read()
        .await;
    let ids = data
        .get::<GuildAndTournamentIDMapContainer>()
        .unwrap()
        .read()
        .await;
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let mut user_ids: Vec<UserId> = Vec::new();
    let mut tourn_name = String::new();
    for ident in args.iter::<String>().quoted().map(|id| id.unwrap()) {
        match user_id_resolver(ctx, msg, &ident).await {
            Some(id) => user_ids.push(id),
            None => {
                tourn_name = ident;
                break;
            }
        };
    }
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    let mut plyr_ids: Vec<PlayerIdentifier> = Vec::with_capacity(user_ids.len());
    for u_id in user_ids {
        match tourn.players.get_right(&u_id) {
            Some(id) => plyr_ids.push(PlayerIdentifier::Id(id.clone())),
            None => {
                msg.reply(
                    &ctx.http,
                    format!(r#"<@{u_id}> is not registered for the tournament."#),
                )
                .await?;
                return Ok(());
            }
        };
    }
    if let Err(err) = tourn.tourn.apply_op(TournOp::CreateRound(plyr_ids)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        // TODO: Finish match creation stuff (role, channels, etc)
        msg.reply(&ctx.http, "Match successfully created!")
            .await?;
    }
    Ok(())
}
