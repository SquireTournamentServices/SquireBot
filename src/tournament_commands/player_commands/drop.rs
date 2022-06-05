use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_core::{operations::TournOp, standard_scoring::PlayerIdentifier};

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

#[command("drop")]
#[only_in(guild)]
#[description("Removes you from the tournament.")]
async fn drop(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    if let Err(err) = tourn
        .tourn
        .apply_op(TournOp::DropPlayer(PlayerIdentifier::Id(player_id)))
    {
        error_to_reply(ctx, msg, err).await?;
    } else {
        msg.reply(&ctx.http, "You have been dropped from the tournament")
            .await?;
    }
    Ok(())
}
