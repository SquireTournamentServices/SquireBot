use dashmap::DashMap;
use serenity::{
    model::id::{GuildId, UserId},
    prelude::*,
};
use std::sync::Arc;

use cycle_map::{CycleMap, GroupMap};
use mtgjson::model::atomics_collection::AtomicCardCollection;
use squire_lib::{
    round::RoundId,
    tournament::{Tournament, TournamentId},
};

use super::{
    confirmation::Confirmation, guild_settings::GuildSettings, guild_tournament::GuildTournament,
    misfortune::Misfortune,
};

pub struct TournamentMapContainer;
impl TypeMapKey for TournamentMapContainer {
    type Value = Arc<DashMap<TournamentId, GuildTournament>>;
}

pub struct GuildSettingsMapContainer;
impl TypeMapKey for GuildSettingsMapContainer {
    type Value = Arc<DashMap<GuildId, GuildSettings>>;
}

pub struct TournamentNameAndIDMapContainer;
impl TypeMapKey for TournamentNameAndIDMapContainer {
    type Value = Arc<RwLock<CycleMap<String, TournamentId>>>;
}

pub struct GuildAndTournamentIDMapContainer;
impl TypeMapKey for GuildAndTournamentIDMapContainer {
    type Value = Arc<RwLock<GroupMap<TournamentId, GuildId>>>;
}

pub struct ConfirmationsContainer;
impl TypeMapKey for ConfirmationsContainer {
    type Value = Arc<DashMap<UserId, Box<dyn Confirmation>>>;
}

pub struct CardCollectionContainer;
impl TypeMapKey for CardCollectionContainer {
    type Value = Arc<RwLock<AtomicCardCollection>>;
}

pub struct MisfortuneUserMapContainer;
impl TypeMapKey for MisfortuneUserMapContainer {
    type Value = Arc<RwLock<GroupMap<UserId, RoundId>>>;
}

pub struct MisfortuneMapContainer;
impl TypeMapKey for MisfortuneMapContainer {
    type Value = Arc<DashMap<RoundId, Misfortune>>;
}
