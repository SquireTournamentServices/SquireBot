use std::fmt::Write;

use serde::{Deserialize, Serialize};
use serenity::{
    builder::CreateEmbed,
    model::{
        channel::{Channel, ChannelCategory, ChannelType, GuildChannel},
        guild::{Guild, Role},
        id::{GuildId, RoleId},
    },
    prelude::Mentionable,
};

use squire_lib::{
    operations::TournOp, settings::TournamentSettingsTree, tournament::TournamentPreset,
};

use crate::{
    model::{consts::*, guild_tournament::GuildTournament, tourn_settings_tree},
    utils::stringify::stringify_option,
};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GuildSettings {
    pub pairings_channel: Option<GuildChannel>,
    pub judge_role: Option<RoleId>,
    pub tourn_admin_role: Option<RoleId>,
    pub matches_category: Option<ChannelCategory>,
    pub make_vc: bool,
    pub make_tc: bool,
    pub tourn_settings: TournamentSettingsTree,
    pub guild_id: GuildId,
}

impl GuildSettings {
    pub fn new(guild_id: GuildId) -> Self {
        GuildSettings {
            guild_id,
            pairings_channel: None,
            judge_role: None,
            tourn_admin_role: None,
            matches_category: None,
            make_vc: true,
            make_tc: false,
            tourn_settings: TournamentSettingsTree::new(),
        }
    }

    /// Return `None` is the server is not configured
    pub fn create_tournament(
        &self,
        tourn_role: Role,
        preset: TournamentPreset,
        name: String,
    ) -> Option<GuildTournament> {
        if self.is_configured() {
            let mut tourn = GuildTournament::new(
                self.guild_id,
                tourn_role,
                self.judge_role.unwrap(),
                self.tourn_admin_role.unwrap(),
                self.pairings_channel.as_ref().unwrap().clone(),
                self.matches_category.as_ref().unwrap().clone(),
                self.make_vc,
                self.make_tc,
                preset,
                String::from("Pioneer"),
                name,
            );
            // Basic settings
            for op in self.tourn_settings.as_settings(preset) {
                let _ = tourn
                    .tourn
                    .apply_op(TournOp::UpdateTournSetting(*SQUIRE_ACCOUNT_ID, op));
            }
            Some(tourn)
        } else {
            None
        }
    }

    pub fn from_existing(guild: &Guild) -> Self {
        let judge_role: Option<RoleId> = get_default_judge_role_id(guild);
        let tourn_admin_role: Option<RoleId> = get_default_tourn_admin_role_id(guild);
        let pairings_channel: Option<GuildChannel> = get_default_pairings_channel_id(guild);
        let matches_category: Option<ChannelCategory> = get_default_matches_category_id(guild);

        GuildSettings {
            guild_id: guild.id,
            pairings_channel,
            judge_role,
            tourn_admin_role,
            matches_category,
            make_vc: true,
            make_tc: false,
            tourn_settings: TournamentSettingsTree::new(),
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
        match &self.pairings_channel {
            Some(c) => {
                if !guild.channels.contains_key(&c.id) {
                    self.pairings_channel = None;
                }
            }
            None => {
                self.pairings_channel = get_default_pairings_channel_id(guild);
            }
        }
        match &self.matches_category {
            Some(c) => {
                if !guild.channels.contains_key(&c.id) {
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

    pub fn populate_embed(&self, embed: &mut CreateEmbed) {
        let _data = String::new();
        "Pairings Channel:\nJudge Role:\nTourn Admin Role:\nMatches Category:\nMake VC:\nMake TC:";
        let mut data = String::new();
        let _ = writeln!(
            data,
            "Judge Role: {}",
            stringify_option(&self.judge_role.as_ref().map(|r| r.mention()))
        );
        let _ = writeln!(
            data,
            "Tourn Admin Role: {}",
            stringify_option(&self.tourn_admin_role.as_ref().map(|r| r.mention()))
        );
        let _ = writeln!(
            data,
            "Pairings Channel: {}",
            stringify_option(&self.pairings_channel.as_ref().map(|c| c.mention()),)
        );
        let _ = writeln!(
            data,
            "Matches Category: {}",
            stringify_option(&self.matches_category.as_ref().map(|c| c.mention()),)
        );
        let _ = writeln!(data, "VCs?: {}", if self.make_vc { "yes" } else { "no" });
        let _ = write!(data, "TCs?: {}", if self.make_tc { "yes" } else { "no" });
        tourn_settings_tree::populate_embed(
            &self.tourn_settings,
            embed
                .title("Default Tournament Settings:")
                .field("Server Settings:", data, true),
        );
    }
}

pub fn get_default_judge_role_id(guild: &Guild) -> Option<RoleId> {
    guild
        .roles
        .iter()
        .filter(|(_, r)| r.name == DEFAULT_JUDGE_ROLE_NAME)
        .map(|(id, _)| *id)
        .next()
}

pub fn get_default_tourn_admin_role_id(guild: &Guild) -> Option<RoleId> {
    guild
        .roles
        .iter()
        .filter(|(_, r)| r.name == DEFAULT_TOURN_ADMIN_ROLE_NAME)
        .map(|(id, _)| *id)
        .next()
}

pub fn get_default_pairings_channel_id(guild: &Guild) -> Option<GuildChannel> {
    guild
        .channels
        .iter()
        .filter_map(|(_, c)| match c {
            Channel::Guild(g_channel) => Some(g_channel),
            _ => None,
        })
        .find(|c| c.kind == ChannelType::Text && c.name == DEFAULT_PAIRINGS_CHANNEL_NAME)
        .cloned()
}

pub fn get_default_matches_category_id(guild: &Guild) -> Option<ChannelCategory> {
    guild
        .channels
        .iter()
        .filter_map(|(_, c)| match c {
            Channel::Category(c_channel) => Some(c_channel),
            _ => None,
        })
        .find(|c| c.kind == ChannelType::Category && c.name == DEFAULT_MATCHES_CATEGORY_NAME)
        .cloned()
}
