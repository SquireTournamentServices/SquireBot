use std::{collections::HashMap, time::Duration};

use serenity::http::CacheHttp;

use squire_lib::{
    identifiers::PlayerId,
    rounds::{RoundId, RoundResult, RoundStatus},
};
use tokio::sync::mpsc::UnboundedReceiver;

use crate::model::guilds::TrackingRound;

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
    ForceConfirmed,
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

    pub fn add_match(&mut self, rnd: TrackingRound) {
        self.matches.insert(rnd.round.round.id, rnd);
    }

    /// Updates match statuses for all stored matches
    pub async fn update_matches(&mut self, cache: impl CacheHttp) {
        self.update();
        let mut drops: Vec<RoundId> = Vec::new();
        for (r_id, m) in self.matches.iter_mut() {
            m.update_message(&cache).await;
            m.send_warning(&cache).await;
            if !m.round.round.is_active() {
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
                    if let Some(m) = self.matches.get_mut(&update.id) {
                        m.round.round.time_extension(dur);
                    }
                }
                RecordResult(result) => {
                    if let Some(m) = self.matches.get_mut(&update.id) {
                        let _ = m.round.round.record_result(result);
                    }
                }
                RecordConfirmation(p_id) => {
                    if let Some(m) = self.matches.get_mut(&update.id) {
                        let _ = m.round.round.confirm_round(p_id);
                    }
                }
                ForceConfirmed => {
                    if let Some(m) = self.matches.get_mut(&update.id) {
                        m.round.round.status = RoundStatus::Certified;
                    }
                }
                DropPlayer(p_id) => {
                    if let Some(m) = self.matches.get_mut(&update.id) {
                        m.round.round.drop_player(&p_id);
                    }
                }
                MatchCancelled => {
                    if let Some(mut m) = self.matches.remove(&update.id) {
                        m.round.round.kill_round();
                    }
                }
            }
        }
    }
}
