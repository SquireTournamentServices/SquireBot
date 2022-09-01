use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_lib::{
    identifiers::AdminId,
    operations::{OpData, TournOp},
    player_registry::PlayerIdentifier,
};

use crate::{
    model::{
        consts::SQUIRE_ACCOUNT_ID,
        containers::{
            GuildAndTournamentIDMapContainer, TournamentMapContainer,
            TournamentNameAndIDMapContainer,
        },
        guild_tournament::RoundCreationFailure,
    },
    utils::{
        error_to_reply::error_to_reply,
        spin_lock::spin_mut,
        tourn_resolver::{admin_tourn_id_resolver, user_id_resolver},
    },
};

#[command("create-match")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("<player name/mention>, ..., [tournament name]")]
#[example("'PlayerA', 'PlayerB'")]
#[example("@PlayerA, @PlayerB")]
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap().read().await;
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let mut raw_players: Vec<String> = args.iter::<String>().quoted().filter_map(|a| a.ok()).collect();
    let tourn_name: String = raw_players.last().cloned().unwrap_or_default();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => {
            if name_and_id.get_right(&tourn_name).is_some() {
                raw_players.pop();
            }
            id
        },
        None => {
            return Ok(());
        }
    };
    let mut tourn = spin_mut(&all_tourns, &tourn_id).await.unwrap();
    let mut plyr_ids: Vec<PlayerIdentifier> = Vec::with_capacity(raw_players.len());
    for plyr in raw_players {
        let plyr_id = match user_id_resolver(ctx, msg, &plyr).await {
            Some(user_id) => {
                match tourn.players.get_right(&user_id) {
                    Some(id) => id.clone().into(),
                    None => {
                        msg.reply(
                            &ctx.http,
                            "That player is not registered for the tournament.",
                        )
                        .await?;
                        return Ok(());
                    }
                }
            },
            None => {
                match tourn.guests.get_right(&plyr) {
                    Some(id) => id.clone().into(),
                    None => {
                        msg.reply(
                            &ctx.http,
                            "That guest is not registered for the tournament. You may have mistyped their name.",
                        )
                        .await?;
                        return Ok(());
                    }
                }
            }
        };
        plyr_ids.push(plyr_id);
    }
    match tourn.tourn.apply_op(TournOp::CreateRound(*SQUIRE_ACCOUNT_ID, plyr_ids)) {
        Err(err) => {
            error_to_reply(ctx, msg, err).await?;
        }
        Ok(data) => {
            tourn.update_status = true;
            if let OpData::CreateRound(ident) = data {
                let rnd = tourn.tourn.get_round(&ident).unwrap();
                let num = rnd.match_number;
                match tourn
                    .create_round_data(&ctx.http, &msg.guild(&ctx.cache).unwrap(), &ident, num)
                    .await
                {
                    Ok(_) => {
                        for plyr in rnd.players {
                            if let Some(user) = tourn
                                .players
                                .get_left(&plyr)
                            {
                                let _ = msg
                                    .guild(ctx)
                                    .unwrap()
                                    .member(ctx, user)
                                    .await
                                    .unwrap()
                                    .add_role(ctx, tourn.match_roles.get(&ident).unwrap())
                                    .await;
                            }
                        }
                        msg.reply(&ctx.http, "Match successfully created!").await?;
                    }
                    Err(e) => {
                        let content = format!("The match was created, but there was an issue creating the {e} in Discord.");
                    }
                }
            }
        }
    }
    Ok(())
}
