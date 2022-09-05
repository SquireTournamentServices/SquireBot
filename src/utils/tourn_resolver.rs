use std::str::FromStr;

use dashmap::DashMap;
use serenity::{
    framework::standard::{macros::hook, CommandError},
    gateway::WebSocketGatewayClientExt,
    model::{channel::Message, id::UserId, mention::Mention},
    prelude::Context,
};

use cycle_map::CycleMap;
use squire_lib::{
    identifiers::PlayerId,
    player_registry::PlayerIdentifier,
    tournament::{Tournament, TournamentId},
};

use crate::{
    model::{guild_tournament::GuildTournament, lookup_error::LookupError},
    utils::spin_lock::spin,
};

#[hook]
/// Given a command context, the inciting message, and an identifier for a user, this method
/// attempts to find a unique user in the guild that matches the ident.
/// This resolver tries to make the following assumptions in order.
///  - An ident that is a valid `u64` is assumed to be a UserId
///  - The given ident is assumed to be a mention.
///  - The given ident is assumed to be a part of a user's nickname
///  - The given ident is assumed to be a part of the user's user name.
///  - The given ident is assumed to be invalid.
pub async fn user_id_resolver(ctx: &Context, msg: &Message, ident: &str) -> Option<UserId> {
    if let Ok(id) = ident.parse::<u64>() {
        Some(UserId(id))
    } else {
        if let Ok(mention) = Mention::from_str(ident) {
            return match mention {
                Mention::User(id) => Some(id),
                _ => None,
            };
        }
        let gld = msg.guild(&ctx.cache).unwrap();
        let by_nickname = gld.members_nick_containing(ident, false, false).await;
        if by_nickname.len() == 1 {
            return Some(by_nickname[0].0.user.id);
        }
        let by_username = gld.members_username_containing(ident, false, false).await;
        if by_username.len() == 1 {
            Some(by_username[0].0.user.id)
        } else {
            None
        }
    }
}

#[hook]
pub async fn player_tourn_resolver(
    ctx: &Context,
    msg: &Message,
    tourn_name: String,
    all_tourns: &DashMap<TournamentId, GuildTournament>,
    mut ids: impl ExactSizeIterator<Item = &'fut TournamentId> + Send + Sync + 'fut,
) -> Result<Option<TournamentId>, CommandError> {
    let mut opt_tourn_id: Option<TournamentId> = None;
    let mut found_mult = false;
    for id in ids {
        let tourn = spin(all_tourns, id).await.unwrap();
        if tourn.players.contains_left(&msg.author.id) {
            found_mult = opt_tourn_id.is_some();
            opt_tourn_id = Some(id.clone());
            if tourn.tourn.name == tourn_name {
                break;
            }
        }
    }
    match opt_tourn_id {
        Some(id) => {
            if found_mult {
                msg.reply(
                    &ctx.http,
                    "You are in multiple tournament. Please specify the name of one of them.",
                )
                .await?;
                return Ok(None);
            }
            Ok(Some(id))
        }
        None => {
            msg.reply(&ctx.http, "You are not registered for any tournament here.")
                .await?;
            return Ok(None);
        }
    }
}

#[hook]
pub async fn admin_tourn_id_resolver(
    ctx: &Context,
    msg: &Message,
    name: &str,
    name_and_id: &CycleMap<String, TournamentId>,
    mut ids: impl ExactSizeIterator<Item = TournamentId> + Send + Sync + 'fut,
) -> Option<TournamentId> {
    match ids.len() {
        0 => {
            let _ = msg
                .reply(
                    &ctx.http,
                    "There are not tournament happening in this server.",
                )
                .await;
            None
        }
        1 => ids.next(),
        _ => {
            // Check name
            if let Some(id) = ids.find(|id| name_and_id.get_left(id).unwrap() == name) {
                Some(id)
            } else {
                let _ = msg.reply(
                    &ctx.http,
                    "There are multiple tournament happening in this server. Please include the name of the tournament.",
                )
                    .await;
                None
            }
        }
    }
}

#[hook]
pub async fn tourn_id_resolver(
    ctx: &Context,
    msg: &Message,
    name: &str,
    name_and_id: &CycleMap<String, TournamentId>,
    mut ids: impl ExactSizeIterator<Item = TournamentId> + Send + 'fut,
) -> Option<TournamentId> {
    let length = ids.len();
    match length {
        0 => {
            let _ = msg
                .reply(
                    &ctx.http,
                    "There are no tournaments being held in this server.",
                )
                .await;
            None
        }
        1 => Some(ids.next().unwrap()),
        _ => {
            if let Some(t_id) = ids.find(|t_id| name_and_id.get_left(t_id).unwrap() == name) {
                Some(t_id)
            } else {
                let _ = msg
                    .reply(
                        &ctx.http,
                        "There is no tournament in this server with that name.",
                    )
                    .await;
                None
            }
        }
    }
}

pub fn player_name_resolver(
    id: PlayerId,
    plyrs: &CycleMap<UserId, PlayerId>,
    tourn: &Tournament,
) -> String {
    if let Some(u_id) = plyrs.get_left(&id) {
        format!("<@{u_id}>\n")
    } else {
        format!(
            "{}\n",
            tourn.get_player(&PlayerIdentifier::Id(id)).unwrap().name
        )
    }
}
