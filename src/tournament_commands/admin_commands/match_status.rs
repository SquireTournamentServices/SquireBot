use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use itertools::Itertools;

use squire_lib::{
    operations::TournOp, player_registry::PlayerIdentifier, round::RoundResult,
    round_registry::RoundIdentifier,
};

use crate::{
    model::{
        consts::SQUIRE_ACCOUNT_ID,
        containers::{
        GuildAndTournamentIDMapContainer, TournamentMapContainer, TournamentNameAndIDMapContainer},
    },
    utils::{
        error_to_reply::error_to_reply,
        spin_lock::spin,
        tourn_resolver::{player_name_resolver, admin_tourn_id_resolver, user_id_resolver},
    },
};

#[command("match-status")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<match #>, [tournament name]")]
#[example("10")]
#[description("Prints an embed of the status of a match.")]
async fn match_status(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let round_number = match args.single::<u64>() {
        Ok(n) => RoundIdentifier::Number(n),
        Err(_) => {
            msg.reply(
                &ctx.http,
                "The first argument must be a proper match number.",
            )
            .await?;
            return Ok(());
        }
    };
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let tourn = spin(&all_tourns, &tourn_id).await.unwrap();
    let round = match tourn.tourn.get_round(&round_number) {
        Ok(rnd) => rnd,
        Err(err) => {
            error_to_reply(ctx, msg, err).await?;
            return Ok(());
        }
    };
    let id = round.id;
    let mut message = msg.reply(ctx, "Give me just a moment...").await?;

    let has_table_number = tourn.tourn.use_table_number;
    let vc_id = tourn.match_vcs.get(&id).map(|c| c.id);
    let tc_id = tourn.match_tcs.get(&id).map(|c| c.id);
    let plyrs = &tourn.players;
    let tourn = &tourn.tourn;
    message
        .edit(&ctx, |m| {
            m.content("\u{200b}").embed(|e| {
                e.title(if has_table_number {
                    format!(
                        "Match #{}: Table {}",
                        round.match_number, round.table_number
                    )
                } else {
                    format!("Match #{}:", round.match_number)
                });
                if !round.is_certified() {
                    e.field(
                        "Time left:",
                        format!("{} min", round.time_left().as_secs() / 60),
                        false,
                    );
                } else {
                    e.field(
                        "Winner:",
                        player_name_resolver(round.winner.clone().unwrap(), plyrs, tourn),
                        false,
                    );
                }
                e.field("Status:", round.status.to_string(), false);
                if let Some(vc) = vc_id {
                    e.field("Voice Channel:", format!("<#{vc}>"), false);
                }
                if let Some(tc) = tc_id {
                    e.field("Text Channel:", format!("<#{tc}>"), false);
                }
                e.field(
                    "Players:",
                    round
                        .players
                        .iter()
                        .map(|id| player_name_resolver(id.clone(), plyrs, tourn))
                        .join("\n"),
                    false,
                )
            })
        })
        .await?;
    Ok(())
}
