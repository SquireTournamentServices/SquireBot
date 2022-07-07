use std::fmt::Write;

use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_core::player_registry::PlayerIdentifier;

use crate::model::{
    containers::{
        GuildAndTournamentIDMapContainer, TournamentMapContainer, TournamentNameAndIDMapContainer,
    },
    guild_tournament::GuildTournament,
};

#[command("decks")]
#[usage("[tournament name]")]
#[description("Prints out a summary of your decks.")]
async fn decks(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let name_and_id = data
        .get::<TournamentNameAndIDMapContainer>()
        .unwrap()
        .read()
        .await;
    let gld_tourn_ids = data
        .get::<GuildAndTournamentIDMapContainer>()
        .unwrap()
        .read()
        .await;
    let tourns = data.get::<TournamentMapContainer>().unwrap();
    let user_name = msg.author.id;
    let tourn_name = args.rest().trim().to_string();
    let mut id_iter = gld_tourn_ids
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
    let tourn = all_tourns.get_mut(tourn_id).unwrap();

    let player_id = tourn.players.get_right(&user_name).unwrap().clone();
    let player = tourn
        .tourn
        .get_player(&PlayerIdentifier::Id(player_id))
        .unwrap();
    let decks = player.get_decks();
    let mut response = String::new();

    for deck in decks.keys() {
        let _ = writeln!(response, "{deck}\n");
    }

    msg.reply(&ctx.http, response).await?;

    Ok(())
}
