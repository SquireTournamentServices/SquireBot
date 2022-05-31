use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
    CacheAndHttp,
};

use squire_core::{
    operations::TournOp, player_registry::PlayerIdentifier, round_registry::RoundIdentifier,
};

use crate::{
    model::containers::{
        GuildAndTournamentIDMapContainer, TournamentMapContainer, TournamentNameAndIDMapContainer,
    },
    utils::{
        error_to_reply::error_to_reply,
        stringify::bool_from_string,
        tourn_resolver::{admin_tourn_id_resolver, user_id_resolver},
    },
};

#[command("remove-match")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[description("Adds a match from the tournament.")]
async fn remove_match(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    match tourn.tourn.get_round(&round_number) {
        Ok(rnd) => {
            if rnd.is_certified() {
                msg.reply(
                    &ctx.http,
                    "That round is already certified. No need to give it an extenstion.",
                )
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
    }
    if let Err(err) = tourn
        .tourn
        .apply_op(TournOp::RemoveRound(round_number.clone()))
    {
        error_to_reply(ctx, msg, err).await?;
    } else {
        msg.reply(&ctx.http, "Round successfully deleted").await?;
        tourn.clear_round_data(round_number, &ctx.http).await;
    }
    Ok(())
}
