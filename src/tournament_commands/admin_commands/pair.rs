use std::collections::HashMap;

use serenity::{
    async_trait,
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_lib::{
    identifiers::AdminId,
    operations::{OpData, TournOp},
    player_registry::PlayerIdentifier,
    tournament::TournamentId,
};

use crate::{
    model::{
        confirmation::Confirmation,
        consts::SQUIRE_ACCOUNT_ID,
        containers::{
            ConfirmationsContainer, GuildAndTournamentIDMapContainer, TournamentMapContainer,
            TournamentNameAndIDMapContainer,
        },
    },
    utils::{
        error_to_reply::error_to_reply,
        spin_lock::spin_mut,
        tourn_resolver::{admin_tourn_id_resolver, user_id_resolver},
    },
};

#[command("pair")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("[tournament name]")]
#[description("Pairs the next round of matches.")]
async fn pair(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = spin_mut(&all_tourns, &tourn_id).await.unwrap();
    match tourn.tourn.apply_op(TournOp::PairRound(*SQUIRE_ACCOUNT_ID)) {
        Err(err) => {
            error_to_reply(ctx, msg, err).await?;
        }
        Ok(data) => {
            tourn.update_status = true;
            let mut members: HashMap<UserId, Member> = msg
                .guild(ctx)
                .unwrap()
                .members(&ctx.http, None, None)
                .await
                .unwrap()
                .into_iter()
                .map(|m| (m.user.id, m))
                .collect();
            if let OpData::Pair(rounds) = data {
                for ident in rounds {
                    let rnd = tourn.tourn.get_round(&ident).unwrap();
                    let num = rnd.match_number;
                    match tourn
                        .create_round_data(&ctx.http, &msg.guild(&ctx.cache).unwrap(), &ident, num)
                        .await
                    {
                        Ok(_) => {
                            for plyr in rnd.players {
                                if let Some(member) = tourn
                                    .players
                                    .get_left(&plyr)
                                    .map(|user| members.get_mut(user))
                                    .flatten()
                                {
                                    // TODO: Do something with this result?
                                    let _ = member
                                        .add_role(&ctx.http, tourn.match_roles.get(&ident).unwrap())
                                        .await;
                                }
                            }
                        }
                        Err(_) => { /* TODO: Do something on fail... */ }
                    };
                }
            }
        }
    };
    Ok(())
}
