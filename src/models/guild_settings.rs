use dashmap::DashMap;
use serde::{Deserialize, Serialize};
use serenity::model::{
    channel::{Channel, ChannelCategory, ChannelType, GuildChannel},
    guild::{Guild, Role},
    id::{ChannelId, GuildId, RoleId},
};
use serenity::prelude::*;

const DEFAULT_PAIRINGS_CHANNEL_NAME: &str = "match-pairings";
const DEFAULT_JUDGE_ROLE_NAME: &str = "Judge";
const DEFAULT_TOURN_ADMIN_ROLE_NAME: &str = "Tournament Admin";
const DEFAULT_MATCHES_CATEGORY_NAME: &str = "Matches";

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

    pub fn from_existing(guild: &Guild) -> Self {
        let judge_role: Option<RoleId> = get_default_judge_role_id(guild);
        let tourn_admin_role: Option<RoleId> = get_default_tourn_admin_role_id(guild);
        let pairings_channel: Option<ChannelId> = get_default_pairings_channel_id(guild);
        let matches_category: Option<ChannelId> = get_default_matches_category_id(guild);

        GuildSettings {
            pairings_channel,
            judge_role,
            tourn_admin_role,
            matches_category,
        }
    }

    pub fn update(&mut self, guild: &Guild) {
        match self.judge_role {
            Some(id) => {
                if !guild.roles.contains_key(&id) {
                    self.judge_role = None;
                }
            }
            None => {
                self.judge_role = get_default_judge_role_id(guild);
            }
        }
        match self.tourn_admin_role {
            Some(id) => {
                if !guild.roles.contains_key(&id) {
                    self.tourn_admin_role = None;
                }
            }
            None => {
                self.tourn_admin_role = get_default_tourn_admin_role_id(guild);
            }
        }
        match self.pairings_channel {
            Some(id) => {
                if !guild.channels.contains_key(&id) {
                    self.pairings_channel = None;
                }
            }
            None => {
                self.pairings_channel = get_default_pairings_channel_id(guild);
            }
        }
        match self.matches_category {
            Some(id) => {
                if !guild.channels.contains_key(&id) {
                    self.matches_category = None;
                }
            }
            None => {
                self.matches_category = get_default_matches_category_id(guild);
            }
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

pub fn get_default_judge_role_id(guild: &Guild) -> Option<RoleId> {
    guild
        .roles
        .iter()
        .filter(|(_, r)| r.name == DEFAULT_JUDGE_ROLE_NAME)
        .map(|(id, _)| (*id).clone())
        .next()
}

pub fn get_default_tourn_admin_role_id(guild: &Guild) -> Option<RoleId> {
    guild
        .roles
        .iter()
        .filter(|(_, r)| r.name == DEFAULT_TOURN_ADMIN_ROLE_NAME)
        .map(|(id, _)| (*id).clone())
        .next()
}

pub fn get_default_pairings_channel_id(guild: &Guild) -> Option<ChannelId> {
    guild
        .channels
        .iter()
        .filter_map(|(_, c)| match c {
            Channel::Guild(g_channel) => Some(g_channel),
            _ => None,
        })
        .filter(|c| c.kind == ChannelType::Text && c.name == DEFAULT_PAIRINGS_CHANNEL_NAME)
        .map(|c| c.id.clone())
        .next()
}

pub fn get_default_matches_category_id(guild: &Guild) -> Option<ChannelId> {
    guild
        .channels
        .iter()
        .filter_map(|(_, c)| match c {
            Channel::Category(c_channel) => Some(c_channel),
            _ => None,
        })
        .filter(|c| c.kind == ChannelType::Text && c.name == DEFAULT_MATCHES_CATEGORY_NAME)
        .map(|c| c.id.clone())
        .next()
}
