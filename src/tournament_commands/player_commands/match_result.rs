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
#[sub_commands(draws)]
#[usage("<# of wins>, [match number], [tournament name]")]
#[example("2")]
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
    let wins = match args.single::<u8>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please include the number of time you won.")
                .await?;
            return Ok(());
        },
        Ok(s) => s,
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
    let rounds = tourn.tourn.round_reg.get_player_active_rounds(&player_id.into());
    let round_number = match rounds.len() {
        1 => RoundIdentifier::Number(rounds[0].match_number),
        0 => {
            msg.reply(&ctx.http, "You are not in an active match in the tournament.")
                .await?;
            return Ok(());
        },
        _ => {
            msg.reply(&ctx.http, "You are in multiple active rounds. Have an admin help you record your result.")
                .await?;
            return Ok(());
        },
    };
    let round_result = RoundResult::Wins(player_id.clone(), wins);
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

#[command("draws")]
#[only_in(guild)]
#[usage("<# of draws>, [tournament name]")]
#[example("2")]
#[description("Submit the number of draws of a match.")]
async fn draws(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let draws = match args.single::<u8>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please include the number of time you won.")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
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
    let rounds = tourn.tourn.round_reg.get_player_active_rounds(&player_id.into());
    let round_number = match rounds.len() {
        1 => RoundIdentifier::Number(rounds[0].match_number),
        0 => {
            msg.reply(&ctx.http, "You are not in an active match in the tournament.")
                .await?;
            return Ok(());
        },
        _ => {
            msg.reply(&ctx.http, "You are in multiple active rounds. Have an admin help you record your result.")
                .await?;
            return Ok(());
        },
    };
    let round_result = RoundResult::Draw(draws);
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
