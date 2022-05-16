use crate::model::{
    containers::{
        GuildAndTournamentIDMapContainer, TournamentMapContainer, TournamentNameAndIDMapContainer,
    },
    guild_tournament::GuildTournament,
};

use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};
use squire_core::{swiss_pairings::TournamentError, tournament::Tournament};

#[command("register")]
#[only_in(guild)]
#[min_args(0)]
#[description("Register for a tournament.")]
async fn register(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    /* Get references to needed data from context */
    let data = ctx.data.read().await;
    let name_and_id = data.get::<TournamentNameAndIDMapContainer>().unwrap();
    let gld_tourns = data.get::<GuildAndTournamentIDMapContainer>().unwrap();
    // Find the TournamentId for the tournament.
    // NOTE: that if there is only one tournament in the guild, we assume the tournament for the
    // player even if they give a name.
    let id_iter = gld_tourns.get_left_iter(&msg.guild_id.unwrap()).unwrap();
    let tourn_id = match id_iter.len() {
        0 => {
            msg.reply(
                &ctx.http,
                "There are no tournaments being held in this server.",
            )
            .await?;
            return Ok(());
        }
        1 => id_iter.next().unwrap(),
        _ => {
            let given_name = args.rest();
            if let Some(t_id) =
                id_iter.find(|t_id| name_and_id.get_left(t_id).unwrap() == given_name)
            {
                t_id
            } else {
                msg.reply(
                    &ctx.http,
                    "There is no tournament in this server with that name.",
                )
                .await?;
                return Ok(());
            }
        }
    };
    // With the tournament id, we can now get the tournament and add them
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let tourn = all_tourns.get_mut(tourn_id).unwrap();
    let plyr_name = msg.author.id.0.to_string();
    // NOTE: The GuildTournament and Tournament structs take care of the nitty-gritty. We just need
    // to inform the player of the outcome. The tournament communicates through TournamentError
    // mostly.
    match tourn.add_player(plyr_name, msg.author.id.clone()) {
        Ok(_) => {
            msg.reply(
                &ctx.http,
                format!("You have been registered for {}", tourn.tourn.name),
            )
            .await?;
        }
        Err(e) => {
            match e {
                TournamentError::IncorrectStatus => {
                    msg.reply(
                        &ctx.http,
                        format!("{} isn't taking new players right now.", tourn.tourn.name),
                    )
                    .await?;
                }
                TournamentError::RegClosed => {
                    msg.reply(
                        &ctx.http,
                        format!("Registertion is closed for {}.", tourn.tourn.name),
                    )
                    .await?;
                }
                TournamentError::PlayerLookup => {
                    // Shouldn't happen as UserIds are unique
                    msg.reply(
                        &ctx.http,
                        "There is already another player with your name. Please enter a new one.",
                    )
                    .await?;
                }
                _ => {
                    // Shouldn't happen unless new errors are added to SquireCore
                    msg.reply(
                        &ctx.http,
                        "There was an issue in registering you for the tournament.",
                    )
                    .await?;
                }
            };
        }
    }
    Ok(())
}
