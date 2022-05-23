use crate::utils::stringify::stringify_option;

use super::guild_tournament::GuildTournament;
use super::{consts::*, tourn_settings_tree::*};

use squire_core::settings::TournamentSetting;

use dashmap::DashMap;
use serde::{Deserialize, Serialize};
use serenity::prelude::*;
use serenity::{
    builder::CreateEmbed,
    model::{
        channel::{Channel, ChannelCategory, ChannelType, GuildChannel},
        guild::{Guild, Role},
        id::{ChannelId, GuildId, RoleId},
    },
};
use squire_core::tournament::TournamentPreset;

use std::collections::HashMap;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GuildSettings {
    pub pairings_channel: Option<ChannelId>,
    pub judge_role: Option<RoleId>,
    pub tourn_admin_role: Option<RoleId>,
    pub matches_category: Option<ChannelId>,
    pub make_vc: bool,
    pub make_tc: bool,
    pub tourn_settings: TournSettingsTree,
}

impl GuildSettings {
    pub fn new() -> Self {
        GuildSettings {
            pairings_channel: None,
            judge_role: None,
            tourn_admin_role: None,
            matches_category: None,
            make_vc: true,
            make_tc: false,
            tourn_settings: TournSettingsTree::new(),
        }
    }

    /// Return `None` is the server is not configured
    pub fn create_tournament(
        &self,
        tourn_role: RoleId,
        preset: TournamentPreset,
        name: String,
    ) -> Option<GuildTournament> {
        if self.is_configured() {
            let tourn = GuildTournament::new(
                tourn_role,
                self.judge_role.unwrap(),
                self.tourn_admin_role.unwrap(),
                self.pairings_channel.unwrap(),
                self.matches_category.unwrap(),
                self.make_vc,
                self.make_tc,
                preset,
                String::from("Pioneer"),
                name,
            );
            // TODO: Apply default settings
            Some(tourn)
        } else {
            None
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
            make_vc: true,
            make_tc: false,
            tourn_settings: TournSettingsTree::new(),
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

    pub fn as_embed(&self, embed: &mut CreateEmbed) {
        let names = "Pairings Channel:\nJudge Role:\nTourn Admin Role:\nMatches Category:\nMake VC:\nMake TC:";
        let mut settings: String =
            (stringify_option(self.judge_role.map_or(None, |c| Some(format!("<@&{}>", c)))) + "\n")
                .to_string();
        settings += &(stringify_option(
            self.tourn_admin_role
                .map_or(None, |c| Some(format!("<@&{}>", c))),
        ) + "\n");
        settings += &(stringify_option(
            self.pairings_channel
                .map_or(None, |c| Some(format!("<#{}>", c))),
        ) + "\n");
        settings += &(stringify_option(
            self.matches_category
                .map_or(None, |c| Some(format!("<#{}>", c))),
        ) + "\n");
        settings += &format!("{}\n{}", self.make_vc, self.make_tc);
        // TODO: Make the settings tree viewable in the embed
        embed
            .title("Server Tournament Settings:")
            .fields(vec![("Settings", names, true), ("Values", &settings, true)]);
    }
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
        .filter(|c| c.kind == ChannelType::Category && c.name == DEFAULT_MATCHES_CATEGORY_NAME)
        .map(|c| c.id.clone())
        .next()
}
