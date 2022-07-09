use serenity::{
    async_trait,
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_lib::{
    operations::{OpData, TournOp},
    player_registry::PlayerIdentifier,
    tournament::TournamentId,
};

use crate::{
    model::{
        confirmation::Confirmation,
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
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
    let mut tourn = spin_mut(all_tourns, &tourn_id).await.unwrap();
    match tourn.tourn.apply_op(TournOp::PairRound()) {
        Err(err) => {
            error_to_reply(ctx, msg, err).await?;
        }
        Ok(data) => {
            tourn.update_status = true;
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
    };
    Ok(())
}
