use std::{collections::HashMap, fmt::Write};

use serenity::{builder::CreateEmbed, model::channel::Message, http::CacheHttp};

use itertools::Itertools;
use serde::{Deserialize, Serialize};

use squire_lib::{identifiers::PlayerId, round::Round};

#[derive(Serialize, Deserialize, Copy, Clone, Default, Debug)]
pub struct TimerWarnings {
    pub five_min: bool,
    pub one_min: bool,
    pub time_up: bool,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct GuildRound {
    pub(crate) round: Round,
    pub(crate) use_table_number: bool,
    pub(crate) round_warnings: TimerWarnings,
    pub(crate) players: HashMap<PlayerId, String>,
    pub(crate) vc_mention: String,
    pub(crate) tc_mention: String,
    pub(crate) role_mention: String,
    pub(crate) match_timers: Message,
}

impl GuildRound {
    pub async fn update_message<'a>(&'a mut self, cache: impl CacheHttp ) {
        self.match_timers.edit(cache, |m| m.embed(|e| self.populate_embed(e))).await;
    }
    
    fn populate_embed(&self, embed: &mut CreateEmbed) -> &mut CreateEmbed {
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
            write!(info, "role: {}", self.role_mention);
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
            fields.push(("Confirmed?:".into(), confirmations, true));
        }
        embed.title(title).fields(fields)
    }
}
