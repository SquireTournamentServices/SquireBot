use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_lib::{error::TournamentError, tournament::Tournament};

use crate::{
    model::{
        containers::{
            GuildAndTournamentIDMapContainer, TournamentMapContainer,
            TournamentNameAndIDMapContainer,
        },
        guild_tournament::GuildTournament,
        lookup_error::LookupError,
    },
    utils::{error_to_reply::error_to_reply, tourn_resolver::tourn_id_resolver},
};

#[command("register")]
#[only_in(guild)]
#[usage("[tournament name]")]
#[description("Register for a tournament.")]
async fn register(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    /* Get references to needed data from context */
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
    // Find the TournamentId for the tournament.
    // NOTE: that if there is only one tournament in the guild, we assume the tournament for the
    // player even if they give a name.
    let id_iter = gld_tourns
        .get_left_iter(&msg.guild_id.unwrap())
        .unwrap()
        .cloned();
    let given_name = args.rest();
    let tourn_id = match tourn_id_resolver(ctx, msg, given_name, &name_and_id, id_iter).await {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    // With the tournament id, we can now get the tournament and add them
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    let plyr_name = msg.author.id.0.to_string();
    // NOTE: The GuildTournament and Tournament structs take care of the nitty-gritty. We just need
    // to inform the player of the outcome. The tournament communicates through TournamentError
    // mostly.
    match tourn.add_player(plyr_name, msg.author.id) {
        Ok(_) => {
            tourn.update_status = true;
            msg.reply(
                &ctx.http,
                format!("You have been registered for {}", tourn.tourn.name),
            )
            .await?;
        }
        Err(e) => {
            error_to_reply(ctx, msg, e).await?;
        }
    }
    Ok(())
}
