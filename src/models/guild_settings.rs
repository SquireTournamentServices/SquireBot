use dashmap::DashMap;
use serde::{Deserialize, Serialize};
use serenity::model::id::{ChannelId, GuildId, RoleId};
use serenity::prelude::*;

#[derive(Serialize, Deserialize, Debug)]
pub struct GuildSettings {
    pairings_channel: Option<ChannelId>,
    judge_role: Option<RoleId>,
    tourn_admin_role: Option<RoleId>,
    matches_category: Option<ChannelId>,
}

impl GuildSettings {
    pub fn new() -> Self {
        GuildSettings {
            pairings_channel: None,
            judge_role: None,
            tourn_admin_role: None,
            matches_category: None,
        }
    }

    pub fn is_configured(&self) -> bool {
        self.pairings_channel.is_some()
            && self.judge_role.is_some()
            && self.tourn_admin_role.is_some()
            && self.matches_category.is_some()
    }
}

pub struct GuildSettingsContainer;

impl TypeMapKey for GuildSettingsContainer {
    type Value = DashMap<GuildId, GuildSettings>;
}
