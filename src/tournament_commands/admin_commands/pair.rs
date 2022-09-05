use std::collections::HashMap;

use serenity::{
    async_trait,
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_lib::{
    identifiers::{AdminId, PlayerId},
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
            if let OpData::Pair(rounds) = data {
                for ident in rounds {
                    let rnd = tourn.tourn.get_round(&ident).unwrap();
                    // I.e is a bye
                    if rnd.is_certified() {
                        let plyr: PlayerId = *rnd.players.iter().next().unwrap();
                        let mention = tourn
                            .get_user_id(&plyr)
                            .map(|p| format!("<@{p}>"))
                            .unwrap_or_else(|| {
                                tourn.guests.get_left(&plyr).cloned().unwrap_or_default()
                            });
                        let _ = tourn
                            .pairings_channel
                            .send_message(&ctx, |m| {
                                m.content(format!("{mention}, you have a bye!"))
                            })
                            .await;
                        continue;
                    }
                    let id = rnd.id;
                    let num = rnd.match_number;
                    match tourn
                        .create_round_data(&ctx.http, &msg.guild(&ctx.cache).unwrap(), &id, num)
                        .await
                    {
                        Ok(_) => {
                            for plyr in rnd.players {
                                if let Some(user_id) = tourn.players.get_left(&plyr) {
                                    // TODO: Do something with this result?
                                    let _ = msg
                                        .guild(ctx)
                                        .unwrap()
                                        .member(ctx, user_id)
                                        .await
                                        .unwrap()
                                        .add_role(ctx, tourn.match_roles.get(&id).unwrap())
                                        .await;
                                }
                            }
                        }
                        Err(e) => {
                            // TODO: Do this properly
                            println!("Issue with round data: {e}");
                        }
                    };
                }
            }
        }
    };
    Ok(())
}
