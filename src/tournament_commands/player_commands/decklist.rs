use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::http::error::ErrorResponse;
use serenity::model::prelude::*;
use serenity::prelude::*;
use serenity::utils::MessageBuilder;
use squire_core::player_registry::PlayerIdentifier;


use crate::model::{
    containers::{
        GuildAndTournamentIDMapContainer, TournamentMapContainer, TournamentNameAndIDMapContainer,
    },
    guild_tournament::GuildTournament,
};

#[command("decklist")]
#[description("Prints out one of your decklists.")]
async fn decklist(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
     /* Get references to needed data from context */
     let data = ctx.data.read().await;
     let name_and_id = data.get::<TournamentNameAndIDMapContainer>().unwrap();
     let gld_tourn_ids = data.get::<GuildAndTournamentIDMapContainer>().unwrap();
     let tourns = data.get::<TournamentMapContainer>().unwrap();
     let user_name = msg.author.id;
     let deck_name = args.single_quoted::<String>().unwrap();
     let tourn_name = args.rest().trim().to_string();
     let id_iter = gld_tourn_ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().filter(|id| tourns.get(id).unwrap().players.contains_left(&msg.author.id));
     let tourn_id = match id_iter.count() {
         0 => {
             msg.reply(
                 &ctx.http,
                 "You are not registered for any tournaments in this server.",
             )
             .await;
             return Ok(());
         },
         1 => id_iter.next().unwrap(),
         _ => {
            if let Some(id) = 
            id_iter.find(|id| name_and_id.get_left(id).unwrap() == &tourn_name) 
            {
                id
            } 
            else 
            {
                msg.reply(
                    &ctx.http,
                    "You are not registered for a tournament with that name."
                )
                .await?;
                return Ok(())
            }
         }
     };
     
     let all_tourns = data.get::<TournamentMapContainer>().unwrap();
     let tourn = all_tourns.get_mut(tourn_id).unwrap();

     let player_id = tourn.players.get_right(&user_name).unwrap().clone();
     let player = tourn.tourn.get_player(&PlayerIdentifier::Id(player_id)).unwrap();
     let response = String::new();
     match player.get_deck(deck_name) {
        Some(Deck) => {
            
        },
        None => {
            msg.reply (
            &ctx.http,
            "Could not find a deck with that name"
            ).await?;
        }
    }
    Ok(())
}