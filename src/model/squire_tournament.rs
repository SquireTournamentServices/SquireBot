use squire_core::swiss_pairings::PlayerId;
use squire_core::tournament::{Tournament, TournamentId};

use dashmap::{DashMap, DashSet};
use serde::{Deserialize, Serialize};
use serenity::model::id::{ChannelId, GuildId, MessageId, RoleId, UserId};
use serenity::prelude::*;

use std::collections::{HashMap, HashSet};
use std::hash::{Hash, Hasher};

#[derive(Debug, Clone)]
pub struct SquireTournament {
    tourn_id: TournamentId,
    tourn_name: String,
    tourn_role: RoleId,
    tourn_status: Option<MessageId>,
    players: HashMap<UserId, PlayerId>,
    match_roles: HashSet<RoleId>,
    match_vcs: HashSet<ChannelId>,
    match_tcs: HashSet<ChannelId>,
    match_timers: HashSet<MessageId>,
    standings_messages: Vec<MessageId>,
}

impl SquireTournament {
    pub fn get_id(&self) -> TournamentId {
        self.tourn_id.clone()
    }

    pub fn get_player_id(&self, user: UserId) -> Option<PlayerId> {
        if let Some(id) = self.players.get(&user) {
            Some(id.clone())
        } else {
            None
        }
    }

    pub fn get_user_id(&self, player: PlayerId) -> Option<UserId> {
        let users: Vec<UserId> = self.players
            .iter()
            .filter(|(_, p)| **p == player)
            .map(|(u, _)| u.clone())
            .collect();
        if users.len() == 1 {
            Some(users[0])
        } else {
            None
        }
    }
}

impl Hash for SquireTournament {
    fn hash<H>(&self, state: &mut H)
    where
        H: Hasher,
    {
        let _ = &self.tourn_id.hash(state);
    }
}
