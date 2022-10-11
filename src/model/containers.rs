use std::{collections::HashMap, sync::Arc};

use dashmap::DashMap;
use serenity::{
    model::id::{GuildId, UserId},
    prelude::*,
};

//use mongodb::Collection;

use cycle_map::{CycleMap, GroupMap};
use mtgjson::model::atomics_collection::AtomicCardCollection;
use squire_lib::{round::RoundId, tournament::{TournamentId, Tournament}};
use tokio::sync::mpsc::UnboundedSender;

use crate::match_manager::MatchUpdateMessage;

use super::{
    confirmation::Confirmation, guild_settings::GuildSettings, guild_tournament::GuildTournament,
};

pub struct TournamentMapContainer;
impl TypeMapKey for TournamentMapContainer {
    type Value = Arc<RwLock<DashMap<TournamentId, GuildTournament>>>;
}

pub struct GuildSettingsMapContainer;
impl TypeMapKey for GuildSettingsMapContainer {
    type Value = Arc<RwLock<DashMap<GuildId, GuildSettings>>>;
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

pub struct MatchUpdateSenderContainer;
impl TypeMapKey for MatchUpdateSenderContainer {
    type Value = Arc<UnboundedSender<MatchUpdateMessage>>;
}

pub struct MisfortuneUserMapContainer;
impl TypeMapKey for MisfortuneUserMapContainer {
    type Value = Arc<RwLock<GroupMap<UserId, RoundId>>>;
}

pub struct DeadTournamentMapContainer;
impl TypeMapKey for DeadTournamentMapContainer {
    type Value = Arc<RwLock<HashMap<TournamentId, GuildTournament>>>;
}

/*
pub struct TournamentCollectionContainer;
impl TypeMapKey for TournamentCollectionContainer {
    type Value = Arc<Collection<Tournament>>;
}

pub struct DeadTournamentCollectionContainer;
impl TypeMapKey for DeadTournamentCollectionContainer {
    type Value = Arc<Collection<Tournament>>;
}

pub struct SettingsCollectionContainer;
impl TypeMapKey for SettingsCollectionContainer {
    type Value = Arc<Collection<GuildSettings>>;
}
*/

//pub struct MisfortuneMapContainer;
//impl TypeMapKey for MisfortuneMapContainer {
//    type Value = Arc<DashMap<RoundId, Misfortune>>;
//}
