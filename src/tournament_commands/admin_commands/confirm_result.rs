use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_lib::{operations::{TournOp, OpData}, player_registry::PlayerIdentifier, round::RoundStatus};

use crate::{
    model::containers::{
        GuildAndTournamentIDMapContainer, TournamentMapContainer, TournamentNameAndIDMapContainer,
    },
    utils::{
        error_to_reply::error_to_reply,
        spin_lock::spin_mut,
        tourn_resolver::{admin_tourn_id_resolver, user_id_resolver},
    },
};

#[command("confirm-result")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<player name/mention>, [tournament name]")]
#[example("'SomePlayer'")]
#[example("@SomePlayer")]
#[description("Confirms a match result on behalf of a player.")]
async fn confirm_result(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let raw_user_id = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(
                &ctx.http,
                "Please include a player, either by name or mention.",
            )
            .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = spin_mut(&all_tourns, &tourn_id).await.unwrap();
    let plyr_id = match user_id_resolver(ctx, msg, &raw_user_id).await {
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
            match tourn.guests.get_right(&raw_user_id) {
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
    match tourn.tourn.apply_op(TournOp::ConfirmResult(plyr_id)) {
        Err(err) => {
            error_to_reply(ctx, msg, err).await?;
        },
        Ok(data) => {
            match data {
                OpData::ConfirmResult(id, status) => {
                    if status == RoundStatus::Certified {
                        tourn.clear_round_data(&id, &ctx.http).await;
                    }
                }
                _ => {
                    unreachable!("Got wrong data back from confirm result");
                }
            }
            tourn.update_status = true;
            tourn.update_standings = true;
            msg.reply(&ctx.http, "Result successfully confirmed!")
                .await?;
        }
    }
    Ok(())
}
