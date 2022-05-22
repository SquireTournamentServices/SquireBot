use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("decklist")]
#[description("Prints out one of your decklists.")]
async fn decklist(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
     /* Get references to needed data from context */
     let data = ctx.data.read().await;
     let name_and_id = data.get::<TournamentNameAndIDMapContainer>().unwrap();
     let gld_tourns = data.get::<GuildAndTournamentIDMapContainer>().unwrap();
     let player_name = msg.author.id.0.to_string();

     let id_iter = gld_tourns.get_left_iter(&msg.guild_id.unwrap()).unwrap();
     let tourn_id = match id_iter.len() {
         0 => {
             msg.reply(
                 &ctx.http,
                 "There are no tournaments being held in this server.",
             )
             .await;
         },
         1 => id_iter.next.unwrap(),
         _ => {
             
         }
     };

     let all_tourns = data.get::<TournamentMapContainer>().unwrap();
     let tourn = all_tourns.get_mut(tourn_id).unwrap();

     if(tourn.players[player_name].decks.len == 0) {
         msg.reply(
             &ctx.http,
             "You have not registered any decks for this tournament"
         )
         .await;
     }

     let names = tourn.players[player_name].decks.names;
     let hashes = tourn.players[player_name].decks.hashes;
     let response = MessageBuilder::new();
     for name in names {
         response
         .push_bold_safe(name)
         .push("\n")
     }
}
