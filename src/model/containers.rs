use std::{collections::HashMap, sync::Arc};

use dashmap::DashMap;
use serenity::{
    model::id::{GuildId, MessageId, UserId},
    prelude::*,
};
use tokio::sync::mpsc::UnboundedSender;

use cycle_map::GroupMap;
use mtgjson::model::atomics_collection::AtomicCardCollection;
use squire_lib::{round::RoundId, tournament::TournamentId};

use crate::{
    logging::LogAction,
    match_manager::MatchUpdateMessage,
    model::{
        confirmation::Confirmation,
        guilds::{GuildTournRegistry, GuildTournament},
    },
};

pub struct GuildTournRegistryMapContainer;
impl TypeMapKey for GuildTournRegistryMapContainer {
    type Value = Arc<RwLock<DashMap<GuildId, GuildTournRegistry>>>;
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

pub struct LogActionSenderContainer;
impl TypeMapKey for LogActionSenderContainer {
    type Value = Arc<UnboundedSender<(MessageId, LogAction)>>;
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
