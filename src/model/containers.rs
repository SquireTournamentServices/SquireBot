use cycle_map::{CycleMap, GroupMap};
use dashmap::DashMap;
use serenity::{
    model::id::{GuildId, UserId},
    prelude::*,
};
use squire_core::{
    round::RoundId,
    tournament::{Tournament, TournamentId},
};

use std::sync::Arc;

use super::{
    guild_settings::GuildSettings, guild_tournament::GuildTournament, misfortune::Misfortune,
};

pub struct TournamentMapContainer;
impl TypeMapKey for TournamentMapContainer {
    type Value = DashMap<TournamentId, GuildTournament>;
}

pub struct GuildSettingsMapContainer;
impl TypeMapKey for GuildSettingsMapContainer {
    type Value = DashMap<GuildId, GuildSettings>;
}

pub struct TournamentNameAndIDMapContainer;
impl TypeMapKey for TournamentNameAndIDMapContainer {
    type Value = Arc<RwLock<CycleMap<String, TournamentId>>>;
}

pub struct GuildAndTournamentIDMapContainer;
impl TypeMapKey for GuildAndTournamentIDMapContainer {
    type Value = Arc<RwLock<GroupMap<TournamentId, GuildId>>>;
}

pub struct MisfortuneUserMapContainer;
impl TypeMapKey for MisfortuneUserMapContainer {
    type Value = Arc<RwLock<GroupMap<UserId, RoundId>>>;
}

pub struct MisfortuneMapContainer;
impl TypeMapKey for MisfortuneMapContainer {
    type Value = DashMap<RoundId, Misfortune>;
}
