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
    utils::{spin_lock::spin_mut, tourn_resolver::player_tourn_resolver},
};

use crate::utils::error_to_reply::error_to_reply;
use squire_core::{operations::TournOp, standard_scoring::PlayerIdentifier};

#[command("confirm-result")]
#[only_in(guild)]
#[usage("[tournament name]")]
#[description("Confirm the result of your match.")]
async fn confirm_result(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    /* Get references to needed data from context */
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
    if let Err(err) = tourn
        .tourn
        .apply_op(TournOp::ConfirmResult(PlayerIdentifier::Id(player_id)))
    {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        tourn.update_standings = true;
        msg.reply(&ctx.http, "Result successfully confirmed!")
            .await?;
    }
    Ok(())
}
