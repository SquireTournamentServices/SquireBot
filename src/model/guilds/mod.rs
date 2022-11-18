use std::collections::{HashMap, HashSet};

use serde::{Deserialize, Serialize};

use serenity::model::{guild::Role, id::GuildId};

use squire_lib::{identifiers::TournamentId, tournament::TournamentPreset};

mod guild_settings;
pub use guild_settings::{
    get_default_judge_role_id, get_default_matches_category_id, get_default_pairings_channel_id,
    get_default_tourn_admin_role_id, GuildSettings,
};

mod guild_rounds;
pub use guild_rounds::{GuildRound, GuildRoundData, TimerWarnings, TrackingRound};

mod guild_tournament;
pub use guild_tournament::{GuildTournament, GuildTournamentAction, SquireTournamentSetting};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GuildTournRegistry {
    guild_id: GuildId,
    pub settings: GuildSettings,
    pub tourns: HashMap<TournamentId, GuildTournament>,
    pub past_tourns: HashSet<TournamentId>,
}

impl GuildTournRegistry {
    pub fn new(id: GuildId) -> Self {
        Self {
            guild_id: id,
            settings: GuildSettings::new(id),
            tourns: HashMap::new(),
            past_tourns: HashSet::new(),
        }
    }

    #[allow(dead_code)]
    pub fn get_tourn(&self, name: &str) -> Option<&GuildTournament> {
        match self.tourns.len() {
            0 => None,
            1 => self.tourns.values().next(),
            _ => self.tourns.values().find(|t| t.tourn.name == name),
        }
    }

    pub fn get_tourn_mut(&mut self, name: &str) -> Option<&mut GuildTournament> {
        match self.tourns.len() {
            0 => None,
            1 => self.tourns.values_mut().next(),
            _ => self.tourns.values_mut().find(|t| t.tourn.name == name),
        }
    }

    pub async fn create_tourn(
        &mut self,
        tourn_role: Role,
        preset: TournamentPreset,
        name: String,
    ) -> bool {
        match self.tourns.values().find(|t| t.tourn.name == name ) {
            Some(_) => false,
            None => match self.settings.create_tournament(tourn_role, preset, name) {
                Some(tourn) => {
                    self.tourns.insert(tourn.tourn.id, tourn);
                    true
                }
                None => false,
            },
        }
    }

    pub async fn remove_tourn(&mut self, id: &TournamentId) -> Option<GuildTournament> {
        let tourn = self.tourns.remove(id)?;
        self.past_tourns.insert(tourn.tourn.id);
        Some(tourn)
    }
}
