use std::collections::HashMap;

use serenity::{
    http::{CacheHttp, Http},
    model::{
        channel::{GuildChannel, Message},
        guild::Role,
    },
};

use serde::{Deserialize, Serialize};

use squire_lib::{identifiers::PlayerId, round::Round};

use crate::utils::{
    embeds::{safe_embeds, StringFields},
    stringify::stringify_option,
};

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
    pub(crate) vc_mention: Option<String>,
    pub(crate) tc_mention: Option<String>,
    pub(crate) role_mention: Option<String>,
}

#[derive(Clone, Debug)]
pub struct TrackingRound {
    pub(crate) round: GuildRound,
    pub(crate) message: Message,
}

impl TrackingRound {
    pub async fn update_message(&mut self, cache: impl CacheHttp) {
        let (title, fields) = self.embed_info();
        let _ = self
            .message
            .edit(cache, |m| m.add_embeds(safe_embeds(title, fields)))
            .await;
    }

    pub async fn send_warning(&mut self, cache: impl CacheHttp) {
        match self.round.round.time_left().as_secs() {
            0 => {
                self.round.warnings.sent_last();
                let _ = self
                    .message
                    .reply(
                        cache,
                        format!("{} time in your match is up!!", self.round.mention()),
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
                            self.round.mention()
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
                            self.round.mention()
                        ),
                    )
                    .await;
            }
            _ => {}
        }
    }

    pub fn embed_info(&self) -> (String, StringFields) {
        self.round.embed_info()
    }
}

impl GuildRound {
    pub fn mention(&self) -> String {
        self.role_mention
            .clone()
            .unwrap_or_else(|| format!("Match #{}", self.round.match_number))
    }

    pub fn embed_info(&self) -> (String, StringFields) {
        let title = if self.use_table_number {
            format!(
                "Match #{}: Table {}",
                self.round.match_number, self.round.table_number
            )
        } else {
            format!("Match #{}:", self.round.match_number)
        };
        let mut fields: Vec<(String, Vec<String>, &'static str, bool)> = Vec::new();
        if !self.round.is_certified() {
            fields.push((
                "Time left:".into(),
                vec![format!("{} min", self.round.time_left().as_secs() / 60)],
                "",
                true,
            ));
        } else {
            fields.push((
                "Winner:".into(),
                vec![self
                    .round
                    .winner
                    .as_ref()
                    .and_then(|w| self.players.get(w).cloned())
                    .unwrap_or_else(|| "None".into())],
                "",
                true,
            ));
        }
        fields.push((
            "Status:".into(),
            vec![self.round.status.to_string()],
            "",
            true,
        ));
        let info = vec![
            format!("Role: {}", stringify_option(&self.role_mention)),
            format!("VC: {}", stringify_option(&self.vc_mention)),
            format!("Text: {}", stringify_option(&self.tc_mention)),
        ];
        fields.push(("Info:".into(), info, " ", true));
        fields.push((
            "Players:".into(),
            self.players.values().cloned().collect(),
            " ",
            true,
        ));
        let mut results: Vec<String> = self
            .players
            .iter()
            .map(|(id, p)| {
                format!(
                    "{p}: {}",
                    self.round.results.get(id).cloned().unwrap_or_default()
                )
            })
            .collect();
        results.push(format!(" draws: {}", self.round.draws));
        fields.push(("Results:".into(), results, " ", true));
        let confirmations = self
            .players
            .iter()
            .map(|(id, p)| format!("{p}: {}", self.round.confirmations.contains(id)))
            .collect();
        fields.push(("Confirmed:".into(), confirmations, " ", true));
        if !self.round.drops.is_empty() {
            let drops = self
                .round
                .drops
                .iter()
                .map(|p| self.players.get(p).unwrap().to_string())
                .collect();
            fields.push(("Drops:".into(), drops, " ", true));
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
