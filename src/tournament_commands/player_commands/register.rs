use crate::model::guild_tournaments::{GuildTournaments, GuildTournamentsContainer};
use crate::model::squire_tournament::SquireTournament;
use crate::model::tournament_container::TournamentContainer;

use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;
use squire_core::swiss_pairings::TournamentError;
use squire_core::tournament::Tournament;
use squire_core::tournament_registry::TournIdentifier;

#[command("register")]
#[only_in(guild)]
#[min_args(0)]
#[max_args(1)]
#[description("Register for a tournament.")]
async fn register(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let all_tourns = data.get::<TournamentContainer>().unwrap();
    let gld_tourns = data.get::<GuildTournamentsContainer>().unwrap();
    let local_tourns = gld_tourns.get(&msg.guild_id.unwrap()).unwrap();
    if let Some(mut s_tourn) = local_tourns.get_only_tourn_mut() {
        let id = s_tourn.get_id();
        let tourn = all_tourns
            .get_mut_tourn(TournIdentifier::Id(id.clone()))
            .unwrap();
        let plyr_name = msg.author.id.0.to_string();
        register_and_reply(ctx, msg, s_tourn.value_mut(), &tourn, plyr_name).await?;
    } else if let Ok(name) = args.single::<String>() {
        if let Some(mut s_tourn) = local_tourns.get_tourn_mut(name) {
            let id = s_tourn.get_id();
            let tourn = all_tourns
                .get_mut_tourn(TournIdentifier::Id(id.clone()))
                .unwrap();
            let plyr_name = msg.author.id.0.to_string();
            register_and_reply(ctx, msg, s_tourn.value_mut(), &tourn, plyr_name).await?;
        } else {
            msg.reply(&ctx.http, "The tournament you named can't be found in this server. Use `!tournaments` to see the names of the tournaments in this server.").await?;
        }
    } else {
        msg.reply(&ctx.http, "The right tournament couldn't be found. Please use `!tournaments` to see the names of tournaments in this server.").await?;
    }
    Ok(())
}

async fn register_and_reply(
    ctx: &Context,
    msg: &Message,
    s_tourn: &mut SquireTournament,
    tourn: &Tournament,
    name: String,
) -> CommandResult {
    match tourn.register_player(name) {
        Ok(id) => {
            s_tourn.add_player(msg.author.id.clone(), id);
            msg.reply(
                &ctx.http,
                format!("You have been registered for {}", tourn.name),
            )
            .await?;
        }
        Err(e) => {
            match e {
                TournamentError::IncorrectStatus => {
                    msg.reply(
                        &ctx.http,
                        format!("{} isn't taking new players right now.", tourn.name),
                    )
                    .await?;
                }
                TournamentError::RegClosed => {
                    msg.reply(
                        &ctx.http,
                        format!("Registertion is closed for {}.", tourn.name),
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
