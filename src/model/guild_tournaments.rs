use super::squire_tournament::SquireTournament;

use squire_core::tournament::Tournament;

use dashmap::DashMap;
use serde::{Deserialize, Serialize};
use serenity::model::id::{ChannelId, GuildId, RoleId};
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
}

impl TypeMapKey for GuildTournamentsContainer {
    type Value = DashMap<GuildId, GuildTournaments>;
}
