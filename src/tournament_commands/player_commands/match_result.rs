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
    utils::error_to_reply::error_to_reply,
};

use squire_core::{
    operations::TournOp, round::RoundResult, round_registry::RoundIdentifier,
    standard_scoring::PlayerIdentifier,
};

#[command("match-result")]
#[only_in(guild)]
#[description("Submit the result of a match.")]
async fn match_result(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let name_and_id = data
        .get::<TournamentNameAndIDMapContainer>()
        .unwrap()
        .read()
        .await;
    let gld_tourns = data
        .get::<GuildAndTournamentIDMapContainer>()
        .unwrap()
        .read()
        .await;

    let tourns = data.get::<TournamentMapContainer>().unwrap();
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
    let mut id_iter = gld_tourns
        .get_left_iter(&msg.guild_id.unwrap())
        .unwrap()
        .filter(|id| {
            tourns
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

    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut tourn = all_tourns.get_mut(tourn_id).unwrap();
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
