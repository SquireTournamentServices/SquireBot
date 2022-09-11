use std::{collections::HashMap, sync::mpsc::Receiver, time::Duration};

use squire_lib::{
    identifiers::PlayerId,
    round::{RoundId, RoundResult},
};

use crate::model::timer_warnings::GuildRound;

/// The update, round pair to be sent to the match manager
pub struct MatchUpdateMessage {
    pub id: RoundId,
    pub update: MatchUpdate,
}

/// The type of update being sent to the match
pub enum MatchUpdate {
    TimeExtention(Duration),
    RecordResult(RoundResult),
    RecordConfirmation(PlayerId),
    DropPlayer(PlayerId),
    MatchCancelled,
}

/// The struct that manages sending updates to active matches.
pub struct MatchManager {
    channel: Receiver<MatchUpdateMessage>,
    matches: HashMap<RoundId, GuildRound>,
}

impl MatchManager {
    /// Creates a new match manager
    pub fn new(channel: Receiver<MatchUpdateMessage>) -> Self {
        todo!()
    }

    /// Processes updates sent in the channel
    fn update(&mut self) {
        use MatchUpdate::*;
        self.channel
            .try_iter()
            .filter_map(|update| self.matches.get_mut(&update.id).map(|m| (m, update.update)))
            .for_each(|(m, update)| match update {
                TimeExtention(dur) => {
                    m.round.time_extension(dur);
                }
                RecordResult(result) => {
                    m.round.record_result(result);
                }
                RecordConfirmation(p_id) => {
                    m.round.confirm_round(p_id);
                }
                DropPlayer(p_id) => {
                    m.round.remove_player(p_id);
                }
                MatchCancelled => {
                    m.round.kill_round();
                }
            });
    }

    /// Updates match statuses for all stored matches
    pub async fn update_matches(&mut self) {
        self.update();
        let mut drops: Vec<RoundId> = Vec::new();
        for (r_id, m) in self.matches.iter_mut() {
            if !m.round.is_active() {
                drops.push(r_id);
            }
        }
        todo!()
    }
}
