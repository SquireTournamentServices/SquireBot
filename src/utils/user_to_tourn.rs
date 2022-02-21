use std::sync::RwLockReadGuard;

use crate::model::{guild_tournaments::{GuildTournaments, GuildTournamentsContainer}, lookup_error::LookupError, misfortune::*, squire_tournament::SquireTournament, tournament_container::TournamentContainer};

use dashmap::{DashMap, mapref::one::Ref};
use serenity::{framework::standard::{macros::hook, Args, CommandResult}, http::Http, model::prelude::*, prelude::*};
use squire_core::tournament_registry::TournamentRegistry;

pub async fn user_to_tourn<'a>(
    all_tourns: &'a TournamentRegistry,
    local_tourns: &'a GuildTournaments,
    http: &'a Http,
    msg: &'a Message,
    args: &'a Args,
    ) -> CommandResult<Ref<'a, String, SquireTournament>> {
    let digest = if args.len() == 0 {
        let (plyr_id, tourn_name) = match local_tourns.get_player_tourn_info(msg.author.id) {
            Err(e) => {
                match &e {
                    LookupError::TooMany => {
                        msg.reply(&http, "You are in multiple tournament in this server. Please specify which tournament you're currently playing in.").await?;
                    }
                    LookupError::NotAny => {
                        msg.reply(&http, "You are not in any tournaments in this server.")
                            .await?;
                        }
                }
                Err(e)?
            }
            Ok((id, name)) => (id, name),
        };
        let t = local_tourns.get_tourn(tourn_name).unwrap();
        Ok(t)
    } else {
        let t = match local_tourns.get_tourn(args.rest().to_string()) {
            None => {
                msg.reply(
                    &http,
                    format!(
                        "There is no tournament in this server called \"{}\"",
                        args.rest()
                    ),
                )
                    .await?;
                Err(LookupError::NotAny)?
            }
            Some(t) => t,
        };
        Ok(t)
    };
    digest
}
