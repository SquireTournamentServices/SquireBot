use std::{collections::HashMap, time::Duration};

use serenity::http::CacheHttp;

use squire_lib::{
    identifiers::PlayerId,
    round::{RoundId, RoundResult},
};
use tokio::sync::mpsc::UnboundedReceiver;

use crate::model::guild_rounds::TrackingRound;

/// The update, round pair to be sent to the match manager
pub struct MatchUpdateMessage {
    pub id: RoundId,
    pub update: MatchUpdate,
}

/// The type of update being sent to the match
pub enum MatchUpdate {
    NewMatch(TrackingRound),
    TimeExtention(Duration),
    RecordResult(RoundResult),
    RecordConfirmation(PlayerId),
    DropPlayer(PlayerId),
    MatchCancelled,
}

/// The struct that manages sending updates to active matches.
pub struct MatchManager {
    channel: UnboundedReceiver<MatchUpdateMessage>,
    matches: HashMap<RoundId, TrackingRound>,
}

impl MatchManager {
    /// Creates a new match manager
    pub fn new(channel: UnboundedReceiver<MatchUpdateMessage>) -> Self {
        Self {
            channel,
            matches: HashMap::new(),
        }
    }

    pub fn populate<I>(&mut self, rnds: I)
    where
        I: Iterator<Item = TrackingRound>,
    {
        self.matches = rnds.map(|t_rnd| (t_rnd.round.id, t_rnd)).collect();
    }

    /// Updates match statuses for all stored matches
    pub async fn update_matches(&mut self, cache: impl CacheHttp) {
        self.update();
        let mut drops: Vec<RoundId> = Vec::new();
        for (r_id, m) in self.matches.iter_mut() {
            m.update_message(&cache).await;
            m.send_warning(&cache).await;
            if !m.round.is_active() {
                drops.push(*r_id);
            }
        }
        drops.into_iter().for_each(|id| {
            self.matches.remove(&id);
        });
    }

    /// Processes updates sent in the channel
    fn update(&mut self) {
        use MatchUpdate::*;
        while let Ok(update) = self.channel.try_recv() {
            match update.update {
                NewMatch(mtch) => {
                    self.matches.insert(update.id, mtch);
                }
                TimeExtention(dur) => {
                    self.matches
                        .get_mut(&update.id)
                        .map(|m| m.round.time_extension(dur));
                }
                RecordResult(result) => {
                    self.matches
                        .get_mut(&update.id)
                        .map(|m| m.round.record_result(result));
                }
                RecordConfirmation(p_id) => {
                    self.matches
                        .get_mut(&update.id)
                        .map(|m| m.round.confirm_round(p_id));
                }
                DropPlayer(p_id) => {
                    self.matches
                        .get_mut(&update.id)
                        .map(|m| m.round.remove_player(p_id));
                }
                MatchCancelled => {
                    self.matches
                        .get_mut(&update.id)
                        .map(|m| m.round.kill_round());
                }
            }
        }
    }
}
