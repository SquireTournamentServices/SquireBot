use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    http::error::ErrorResponse,
    model::prelude::*,
    prelude::*,
    utils::MessageBuilder,
};

use squire_core::player_registry::PlayerIdentifier;

use crate::{
    model::{
        containers::{
            GuildAndTournamentIDMapContainer, TournamentMapContainer,
            TournamentNameAndIDMapContainer,
        },
        guild_tournament::GuildTournament,
    },
    utils::sort_deck::TypeSortedDeck,
};

#[command("decklist")]
#[description("Prints out one of your decklists.")]
async fn decklist(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    /* Get references to needed data from context */
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
    let deck_name = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please include a deck name.").await?;
            return Ok(());
        }
        Ok(s) => s,
    };
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
    let response = String::new();
    match player.get_deck(&deck_name) {
        Some(deck) => {
            let sorted_deck = TypeSortedDeck::from(deck);
            match msg.channel(&ctx.http).await? {
                Channel::Guild(channel) => {
                    channel
                        .send_message(&ctx.http, |m| {
                            m.embed(|e| {
                                sorted_deck
                                    .populate_embed(e)
                                    .title(format!("<@{user_name}>'s Deck: {deck_name}"))
                            })
                        })
                        .await?;
                }
                _ => {
                    msg.reply(&ctx.http, "This command cannot be used here")
                        .await?;
                }
            }
        }
        None => {
            msg.reply(&ctx.http, "Could not find a deck with that name")
                .await?;
        }
    }
    Ok(())
}
