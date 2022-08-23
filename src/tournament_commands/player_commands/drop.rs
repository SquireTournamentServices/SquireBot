use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_lib::{operations::TournOp, identifiers::PlayerIdentifier};

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

#[command("drop")]
#[only_in(guild)]
#[usage("[tournament name]")]
#[description("Removes you from the tournament.")]
async fn drop(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
        .apply_op(TournOp::DropPlayer(PlayerIdentifier::Id(player_id)))
    {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "You have been dropped from the tournament")
            .await?;
    }
    Ok(())
}
