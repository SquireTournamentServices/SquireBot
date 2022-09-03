use std::future::Future;

use serenity::{model::prelude::Message, prelude::Context};

use squire_lib::{
    operations::{OpResult, TournOp},
    player_registry::PlayerIdentifier,
};

use crate::{
    model::{containers::{
        CardCollectionContainer, GuildAndTournamentIDMapContainer, TournamentMapContainer,
        TournamentNameAndIDMapContainer,
    }, guild_tournament::GuildTournament},
    utils::{
        spin_lock::{spin, spin_mut},
        tourn_resolver::{player_tourn_resolver, user_id_resolver},
    },
};

/// Handles 90% of a command.
pub async fn player_command<F, Fut>(
    ctx: &Context,
    msg: &Message,
    tourn_name: String,
    f: F,
) -> Option<OpResult>
where
    F: FnOnce(&mut GuildTournament, PlayerIdentifier) -> Fut,
    Fut: Future<Output = Option<TournOp>>,
{
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap().read().await;
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let tourn_id = player_tourn_resolver(
        ctx,
        msg,
        tourn_name,
        &all_tourns,
        ids.get_left_iter(&msg.guild_id.unwrap()).unwrap(),
    )
    .await?;
    let mut tourn = spin_mut(&all_tourns, &tourn_id).await.unwrap();
    let plyr_id: PlayerIdentifier = match tourn.players.get_right(&msg.author.id) {
        Some(id) => id.clone().into(),
        None => {
            msg.reply(&ctx.http, "You are not registered for that tournament.")
                .await
                .ok()?;
            return None;
        }
    };
    let op = f(&mut tourn, plyr_id).await?;
    Some(tourn.tourn.apply_op(op))
}
