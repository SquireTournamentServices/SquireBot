use super::lookup_error::LookupError;
use super::squire_tournament::SquireTournament;

use dashmap::mapref::one::Ref;
use squire_core::swiss_pairings::PlayerId;
use squire_core::tournament::{Tournament, TournamentId};

use dashmap::DashMap;
use serde::{Deserialize, Serialize};
use serenity::model::id::{ChannelId, GuildId, RoleId, UserId};
use serenity::prelude::*;

pub struct GuildTournaments {
    guild_tourns: DashMap<String, SquireTournament>,
}

pub struct GuildTournamentsContainer;

impl GuildTournaments {
    pub fn new() -> Self {
        GuildTournaments {
            guild_tourns: DashMap::new(),
        }
    }

    pub fn get_tourn(&self, name: String) -> Option<Ref<String, SquireTournament>> {
        self.guild_tourns.get(&name)
    }

    pub fn get_player_tourn_info(&self, user: UserId) -> Result<(PlayerId, String), LookupError> {
        let tourns: Vec<(PlayerId, String)> = self
            .guild_tourns
            .iter()
            .filter_map(|r| {
                r.value()
                    .get_player(user)
                    .map(|p| (p.clone(), r.key().clone()))
            })
            .collect();
        if tourns.len() == 0 {
            Err(LookupError::NotAny)
        } else if tourns.len() > 1 {
            Err(LookupError::TooMany)
        } else {
            Ok(tourns[0].clone())
        }
    }
}

impl TypeMapKey for GuildTournamentsContainer {
    type Value = DashMap<GuildId, GuildTournaments>;
}
