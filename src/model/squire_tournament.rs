use squire_core::tournament::{Tournament, TournamentId};

use dashmap::DashMap;
use serde::{Deserialize, Serialize};
use serenity::model::id::{ChannelId, MessageId, RoleId};
use serenity::prelude::*;

use std::collections::{HashMap, HashSet};
use std::hash::{Hash, Hasher};

#[derive(Debug, Clone)]
pub struct SquireTournament {
    tourn_id: TournamentId,
    tourn_name: String,
    tourn_role: RoleId,
    tourn_status: Option<MessageId>,
    match_roles: HashSet<RoleId>,
    match_vcs: HashSet<ChannelId>,
    match_tcs: HashSet<ChannelId>,
    match_timers: HashSet<MessageId>,
    standings_messages: Vec<MessageId>,
}

impl Hash for SquireTournament {
    fn hash<H>(&self, state: &mut H)
    where
        H: Hasher,
    {
        let _ = &self.tourn_id.hash(state);
    }
}
