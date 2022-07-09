use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_core::{
    operations::{OpData, TournOp},
    player_registry::PlayerIdentifier,
    round_registry::RoundIdentifier,
};

use crate::{
    model::containers::{
        CardCollectionContainer, GuildAndTournamentIDMapContainer, TournamentMapContainer,
        TournamentNameAndIDMapContainer,
    },
    utils::{
        error_to_reply::error_to_reply,
        spin_lock::spin_mut,
        tourn_resolver::{admin_tourn_id_resolver, player_tourn_resolver, user_id_resolver},
    },
};

#[command("ready")]
#[only_in(guild)]
#[aliases("lfg")]
#[usage("[tournament name]")]
#[description("Shows that you're ready to play your next match.")]
async fn ready(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    // Resolve the tournament id
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match player_tourn_resolver(
        ctx,
        msg,
        tourn_name,
        all_tourns,
        ids.get_left_iter(&msg.guild_id.unwrap()).unwrap(),
    )
    .await
    {
        None => {
            return Ok(());
        }
        Some(id) => id,
    };
    let mut tourn = spin_mut(all_tourns, &tourn_id).await.unwrap();
    let plyr_id = match tourn.players.get_right(&msg.author.id) {
        Some(id) => PlayerIdentifier::Id(id.clone()),
        None => {
            msg.reply(&ctx.http, "You are not registered for that tournament.")
                .await?;
            return Ok(());
        }
    };
    match tourn.tourn.apply_op(TournOp::ReadyPlayer(plyr_id)) {
        Err(err) => {
            error_to_reply(ctx, msg, err).await?;
        }
        Ok(data) => {
            tourn.update_status = true;
            msg.reply(&ctx.http, r#"You are marked as "ready to play"!"#)
                .await?;
            if let OpData::Pair(rounds) = data {
                for ident in rounds {
                    let rnd = tourn.tourn.get_round(&ident).unwrap();
                    let num = rnd.match_number;
                    // TODO: We should do something if this fails...
                    let _ = tourn
                        .create_round_data(&ctx.http, &msg.guild(&ctx.cache).unwrap(), &ident, num)
                        .await;
                }
            }
        }
    }
    Ok(())
}

#[command("unready")]
#[only_in(guild)]
#[aliases("leave-lfg")]
#[usage("[tournament name]")]
#[description("Shows that you're not ready to play your next match.")]
async fn unready(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let tourn_name = args.rest().trim().to_string();
    let mut id_iter = ids
        .get_left_iter(&msg.guild_id.unwrap())
        .unwrap()
        .filter(|id| {
            all_tourns
                .get(id)
                .unwrap()
                .players
                .contains_left(&msg.author.id)
        });
    let tourn_id = match id_iter.clone().count() {
        0 => {
            msg.reply(
                &ctx.http,
                "You are not registered for any tournaments in this server.",
            )
            .await?;
            return Ok(());
        }
        1 => id_iter.next().unwrap(),
        _ => {
            if let Some(id) = id_iter.find(|id| name_and_id.get_left(id).unwrap() == &tourn_name) {
                id
            } else {
                msg.reply(
                    &ctx.http,
                    "You are not registered for a tournament with that name.",
                )
                .await?;
                return Ok(());
            }
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    let plyr_id = match tourn.players.get_right(&msg.author.id) {
        Some(id) => PlayerIdentifier::Id(id.clone()),
        None => {
            msg.reply(&ctx.http, "You are not registered for that tournament.")
                .await?;
            return Ok(());
        }
    };
    if let Err(err) = tourn.tourn.apply_op(TournOp::UnReadyPlayer(plyr_id)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Deck successfully added!").await?;
    }
    Ok(())
}
