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

pub struct TournamentIdentMapContainer;
impl TypeMapKey for TournamentIdentMapContainer {
    type Value = DashMap<String, TournamentId>;
}

pub struct GuildTournamentMap;
impl TypeMapKey for GuildTournamentMap {
    type Value = GroupMap<TournamentId, GuildId>;
}

pub struct GuildSettingsMapContainer;
impl TypeMapKey for GuildSettingsMapContainer {
    type Value = DashMap<GuildId, GuildSettings>;
}

pub struct TournamentNameAndIDMapContainer;
impl TypeMapKey for TournamentNameAndIDMapContainer {
    type Value = CycleMap<String, TournamentId>;
}

pub struct GuildAndTournamentIDMapContainer;
impl TypeMapKey for GuildAndTournamentIDMapContainer {
    type Value = GroupMap<TournamentId, GuildId>;
}

pub struct MisfortunePlayerMapContainer;
impl TypeMapKey for MisfortunePlayerMapContainer {
    type Value = DashMap<UserId, RoundId>;
}

pub struct MisfortuneMapContainer;
impl TypeMapKey for MisfortuneMapContainer {
    type Value = DashMap<RoundId, Misfortune>;
}
