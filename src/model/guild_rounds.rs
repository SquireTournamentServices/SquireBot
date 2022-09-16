use std::{collections::HashMap, fmt::Write};

use serenity::{
    http::{CacheHttp, Http},
    model::{
        channel::{GuildChannel, Message},
        guild::Role,
    },
};

use itertools::Itertools;
use serde::{Deserialize, Serialize};

use squire_lib::{identifiers::PlayerId, round::Round};

#[derive(Serialize, Deserialize, Copy, Clone, Default, Debug)]
pub struct TimerWarnings {
    pub five_min: bool,
    pub one_min: bool,
    pub time_up: bool,
}

#[derive(Serialize, Deserialize, Clone, Default, Debug)]
pub struct GuildRoundData {
    pub(crate) message: Option<Message>,
    pub(crate) vc: Option<GuildChannel>,
    pub(crate) tc: Option<GuildChannel>,
    pub(crate) role: Option<Role>,
    pub(crate) warnings: TimerWarnings,
}

#[derive(Clone, Debug)]
pub struct GuildRound {
    pub(crate) round: Round,
    pub(crate) use_table_number: bool,
    pub(crate) warnings: TimerWarnings,
    pub(crate) players: HashMap<PlayerId, String>,
    pub(crate) vc_mention: String,
    pub(crate) tc_mention: String,
    pub(crate) role_mention: String,
}

#[derive(Clone, Debug)]
pub struct TrackingRound {
    pub(crate) round: GuildRound,
    pub(crate) message: Message,
}

impl TrackingRound {
    pub async fn update_message<'a>(&'a mut self, cache: impl CacheHttp) {
        let (title, fields) = self.embed_info();
        let _ = self
            .message
            .edit(cache, |m| m.embed(|e| e.title(title).fields(fields)))
            .await;
    }

    pub async fn send_warning<'a>(&'a mut self, cache: impl CacheHttp) {
        match self.round.round.time_left().as_secs() {
            0 => {
                self.round.warnings.sent_last();
                let _ = self
                    .message
                    .reply(
                        cache,
                        format!("{} time in your match is up!!", self.round.role_mention),
                    )
                    .await;
            }
            1..=60 => {
                self.round.warnings.sent_second();
                let _ = self
                    .message
                    .reply(
                        cache,
                        format!(
                            "{}, you have 1 minute left in your match!!",
                            self.round.role_mention
                        ),
                    )
                    .await;
            }
            61..=300 => {
                self.round.warnings.sent_first();
                let _ = self
                    .message
                    .reply(
                        cache,
                        format!(
                            "{}, you have 5 minutes left in your match!!",
                            self.round.role_mention
                        ),
                    )
                    .await;
            }
            _ => {}
        }
    }

    pub fn embed_info(&self) -> (String, Vec<(String, String, bool)>) {
        self.round.embed_info()
    }
}

impl GuildRound {
    pub fn embed_info(&self) -> (String, Vec<(String, String, bool)>) {
        let title = if self.use_table_number {
            format!(
                "Match #{}: Table {}",
                self.round.match_number, self.round.table_number
            )
        } else {
            format!("Match #{}:", self.round.match_number)
        };
        let mut fields: Vec<(String, String, bool)> = Vec::new();
        if !self.round.is_certified() {
            fields.push((
                "Time left:".into(),
                format!("{} min", self.round.time_left().as_secs() / 60),
                true,
            ));
        } else {
            fields.push((
                "Winner:".into(),
                self.round
                    .winner
                    .as_ref()
                    .map(|w| self.players.get(w).cloned())
                    .flatten()
                    .unwrap_or_else(|| "None".into()),
                true,
            ));
        }
        fields.push(("Status:".into(), self.round.status.to_string(), true));
        let mut info = String::from("\u{200b}");
        if !self.role_mention.is_empty() {
            let _ = write!(info, "role: {}", self.role_mention);
        }
        if !self.vc_mention.is_empty() {
            let _ = write!(info, "VC: {}", self.vc_mention);
        }
        if !self.tc_mention.is_empty() {
            let _ = write!(info, "Text: {}", self.tc_mention);
        }
        fields.push(("Info:".into(), info, true));
        fields.push(("Players:".into(), self.players.values().join(" "), true));
        let mut results = self
            .players
            .iter()
            .map(|(id, p)| {
                format!(
                    "{p}: {}",
                    self.round.results.get(id).cloned().unwrap_or_default()
                )
            })
            .join(" ");
        let _ = write!(results, " draws: {}", self.round.draws);
        fields.push(("Results:".into(), results, true));
        let confirmations = self
            .players
            .iter()
            .map(|(id, p)| format!("{p}: {}", self.round.confirmations.contains(id)))
            .join(" ");
        fields.push(("Confirmed?:".into(), confirmations, true));
        if !self.round.drops.is_empty() {
            let drops = self
                .round
                .drops
                .iter()
                .map(|p| format!("{}", self.players.get(p).unwrap()))
                .join(" ");
            fields.push(("Drops:".into(), drops, true));
        }
        (title, fields)
    }
}

impl GuildRoundData {
    pub async fn delete_guild_data(self, http: &Http) {
        if let Some(tc) = self.tc {
            let _ = tc.delete(http).await;
        }
        if let Some(vc) = self.vc {
            let _ = vc.delete(http).await;
        }
        if let Some(mut role) = self.role {
            let _ = role.delete(http).await;
        }
    }
}

impl TimerWarnings {
    pub fn sent_first(&mut self) {
        self.five_min = true;
    }

    pub fn sent_second(&mut self) {
        self.five_min = true;
        self.one_min = true;
    }

    pub fn sent_last(&mut self) {
        self.five_min = true;
        self.one_min = true;
        self.time_up = true;
    }
}
