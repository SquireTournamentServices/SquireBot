use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use crate::{
    model::{
        containers::{
            GuildAndTournamentIDMapContainer, TournamentMapContainer,
            TournamentNameAndIDMapContainer,
        },
        guild_tournament::GuildTournament,
    },
    utils::{
        error_to_reply::error_to_reply, spin_lock::spin_mut, tourn_resolver::player_tourn_resolver,
    },
};

use squire_lib::{
    operations::TournOp, round::RoundResult, round_registry::RoundIdentifier,
    identifiers::PlayerIdentifier,
};

#[command("match-result")]
#[only_in(guild)]
#[usage("<# of wins/'draw'>, [tournament name]")]
#[example("2")]
#[example("draw")]
#[description("Submit the result of a match.")]
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
    let user_name = msg.author.id;
    let raw_result = match args.single::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please include the number of time you won.")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let round_number = match args.single::<u64>() {
        Ok(n) => RoundIdentifier::Number(n),
        Err(_) => {
            msg.reply(
                &ctx.http,
                "The second argument must be a proper match number.",
            )
            .await?;
            return Ok(());
        }
    };
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
    let player_id = tourn.players.get_right(&user_name).unwrap().clone();
    let round_result = match raw_result.parse::<u8>() {
        Ok(n) => RoundResult::Wins(player_id.clone(), n),
        Err(_) => {
            if raw_result == "draw" {
                RoundResult::Draw()
            } else {
                msg.reply(
                    &ctx.http,
                    "The third argument must be the number of wins for the player.",
                )
                .await?;
                return Ok(());
            }
        }
    };
    match tourn.tourn.get_round(&round_number) {
        Ok(round) => {
            if !round.players.contains(&player_id) {
                msg.reply(&ctx.http, "You are not in that match of the tournament.")
                    .await?;
                return Ok(());
            }
        }
        Err(_) => {
            msg.reply(
                &ctx.http,
                "There is not a round with that match number in the tournament.",
            )
            .await?;
            return Ok(());
        }
    };
    if let Err(err) = tourn
        .tourn
        .apply_op(TournOp::RecordResult(round_number, round_result))
    {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Result successfully confirmed!")
            .await?;
    }
    Ok(())
}
