use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_core::{operations::TournOp, player_registry::PlayerIdentifier, round::RoundResult, round_registry::RoundIdentifier};

use crate::{
    model::containers::{
        GuildAndTournamentIDMapContainer, TournamentMapContainer, TournamentNameAndIDMapContainer,
    },
    utils::{
        error_to_reply::error_to_reply,
        tourn_resolver::{admin_tourn_id_resolver, user_id_resolver},
    },
};

#[command("match-result")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[description("Records the result of a match.")]
async fn match_result(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let raw_user_id = args.single_quoted::<String>().unwrap();
    let user_id = match user_id_resolver(ctx, msg, &raw_user_id).await {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let round_number = match args.single::<u64>() {
        Ok(n) => RoundIdentifier::Number(n),
        Err(_) => {
            msg.reply(&ctx.http, "The second argument must be a proper match number.").await?;
            return Ok(());
        }
    };
    let raw_result = args.single::<String>().unwrap();
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    let plyr_id = match tourn.players.get_right(&user_id) {
        Some(id) => id.clone(),
        None => {
            msg.reply(
                &ctx.http,
                "That player is not registered for the tournament.",
            )
                .await?;
            return Ok(());
        }
    };
    match tourn.tourn.get_round(&round_number) {
        Ok(rnd) => {
            if !rnd.players.contains(&plyr_id) {
                msg.reply(
                    &ctx.http,
                    "That player is not in that match of the tournament.",
                )
                    .await?;
                return Ok(());
            }
        },
        Err(_) => {
            msg.reply(
                &ctx.http,
                "There is not a round with that match number in the tournament.",
            )
                .await?;
            return Ok(());
        }
    }
    let round_result = match raw_result.parse::<u8>() {
        Ok(n) => RoundResult::Wins(plyr_id, n),
        Err(_) => {
            if raw_result == "draw" {
                RoundResult::Draw()
            } else {
                msg.reply(&ctx.http, "The third argument must be the number of wins for the player.").await?;
                return Ok(());
            }
        }
    };
    if let Err(err) = tourn.tourn.apply_op(TournOp::RecordResult(round_number, round_result)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        msg.reply(&ctx.http, "Result successfully recorded!")
            .await?;
    }
    Ok(())
}
