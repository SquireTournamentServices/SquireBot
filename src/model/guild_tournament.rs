#![allow(dead_code)]

use std::{collections::HashMap, fmt};

use serde::{Deserialize, Serialize};

use serenity::{
    framework::standard::CommandResult,
    http::{CacheHttp, Http},
    model::channel::ChannelCategory,
    model::{
        channel::{
            ChannelType, GuildChannel, Message, PermissionOverwrite, PermissionOverwriteType,
        },
        guild::{Guild, Role},
        id::{GuildId, RoleId, UserId},
        Permissions,
    },
    prelude::*,
};

use cycle_map::CycleMap;
use squire_lib::{
    admin::Admin,
    error::TournamentError,
    identifiers::{PlayerId, PlayerIdentifier, RoundIdentifier},
    operations::{OpData, OpResult, TournOp},
    round::RoundId,
    settings::TournamentSetting,
    tournament::{Tournament, TournamentPreset},
};

use crate::{
    model::{consts::SQUIRE_ACCOUNT_ID, guild_rounds::GuildRound},
    utils::embeds::update_status_message,
};

use super::guild_rounds::{TimerWarnings, TrackingRound};

pub enum RoundCreationFailure {
    VC,
    TC,
    Role,
    Message,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum SquireTournamentSetting {
    PairingsChannel(GuildChannel),
    MatchesCategory(ChannelCategory),
    CreateVC(bool),
    CreateTC(bool),
    TournamentSetting(TournamentSetting),
}

pub enum GuildTournamentAction {
    GetRawStandings,
    ViewDecklist(PlayerIdentifier, String),
    ViewPlayerDecks(PlayerIdentifier),
    ViewPlayerProfile(PlayerIdentifier),
    ViewAllPlayers,
    ViewStandings,
    ViewMatchStatus(RoundIdentifier),
    ViewTournamentStatus,
    RegisterPlayer(UserId),
    RegisterGuest(String),
    CreateMatch(Vec<String>),
    Operation(TournOp),
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GuildTournament {
    pub(crate) guild_id: GuildId,
    pub(crate) tourn: Tournament,
    pub(crate) tourn_role: Role,
    pub(crate) judge_role: RoleId,
    pub(crate) tourn_admin_role: RoleId,
    pub(crate) pairings_channel: GuildChannel,
    pub(crate) matches_category: ChannelCategory,
    pub(crate) tourn_status: Option<Message>,
    pub(crate) players: CycleMap<UserId, PlayerId>,
    #[serde(default)]
    pub(crate) guests: CycleMap<String, PlayerId>,
    pub(crate) make_vc: bool,
    pub(crate) make_tc: bool,
    pub(crate) guild_rounds: HashMap<RoundId, GuildRound>,
    pub(crate) standings_message: Option<Message>,
}

impl GuildTournament {
    pub fn new(
        guild_id: GuildId,
        tourn_role: Role,
        judge_role: RoleId,
        tourn_admin_role: RoleId,
        pairings_channel: GuildChannel,
        matches_category: ChannelCategory,
        make_vc: bool,
        make_tc: bool,
        preset: TournamentPreset,
        format: String,
        name: String,
    ) -> Self {
        let mut tourn = Tournament::from_preset(name, preset, format);
        let admin = Admin {
            id: (*SQUIRE_ACCOUNT_ID).into(),
            name: "Squire Bot".into(),
        };
        tourn.admins.insert((*SQUIRE_ACCOUNT_ID).into(), admin);
        Self {
            guild_id,
            tourn_role,
            judge_role,
            tourn_admin_role,
            pairings_channel,
            matches_category,
            make_vc,
            make_tc,
            tourn_status: None,
            players: CycleMap::new(),
            guests: CycleMap::new(),
            guild_rounds: HashMap::new(),
            standings_message: None,
            tourn,
        }
    }

    pub fn update_setting(&mut self, setting: SquireTournamentSetting) -> OpResult {
        use SquireTournamentSetting::*;
        match setting {
            PairingsChannel(channel) => {
                self.pairings_channel = channel;
            }
            MatchesCategory(category) => {
                self.matches_category = category;
            }
            CreateVC(b) => {
                self.make_vc = b;
            }
            CreateTC(b) => {
                self.make_tc = b;
            }
            TournamentSetting(setting) => {
                self.tourn
                    .apply_op(TournOp::UpdateTournSetting(*SQUIRE_ACCOUNT_ID, setting))?;
            }
        };
        Ok(OpData::Nothing)
    }

    #[allow(unused)]
    pub async fn take_action(
        &mut self,
        _ctx: &Context,
        _msg: &Message,
        action: GuildTournamentAction,
    ) -> OpResult {
        use GuildTournamentAction::*;
        match action {
            GetRawStandings => {
                todo!()
            }
            ViewDecklist(p_ident, deck_name) => {
                todo!()
            }
            ViewPlayerDecks(p_ident) => {
                todo!()
            }
            ViewPlayerProfile(p_ident) => {
                todo!()
            }
            ViewAllPlayers => {
                todo!()
            }
            ViewStandings => {
                todo!()
            }
            ViewMatchStatus(r_ident) => {
                todo!()
            }
            ViewTournamentStatus => {
                todo!()
            }
            RegisterPlayer(user_id) => {
                todo!()
            }
            RegisterGuest(name) => {
                todo!()
            }
            CreateMatch(raw_plyrs) => {
                todo!()
            }
            Operation(op) => {
                todo!()
            }
        }
    }

    pub fn get_player_id(&self, user: &UserId) -> Option<PlayerId> {
        self.players.get_right(user).cloned()
    }

    pub fn get_tracking_round(&self, r_id: &RoundId) -> Option<TrackingRound> {
        let round = self.tourn.get_round(&(*r_id).into()).ok()?;
        let g_rnd = self.guild_rounds.get(r_id).cloned()?;
        let message = g_rnd.message?;
        let players = round
            .players
            .iter()
            .filter_map(|p| {
                self.players
                    .get_left(p)
                    .map(|u| u.mention().to_string())
                    .or_else(|| self.guests.get_left(p).cloned())
                    .map(|s| (*p, s))
            })
            .collect();
        let vc_mention = g_rnd.vc.map(|vc| vc.mention().to_string()).unwrap_or_default();
        let tc_mention = g_rnd.tc.map(|tc| tc.mention().to_string()).unwrap_or_default();
        let role_mention = g_rnd.role.map(|role| role.mention().to_string()).unwrap_or_default();
        Some(TrackingRound {
            round,
            message,
            players,
            vc_mention,
            tc_mention,
            role_mention,
            warnings: TimerWarnings::default(),
            use_table_number: self.tourn.use_table_number,
        })
    }

    pub async fn create_round_data(
        &mut self,
        cache: &impl CacheHttp,
        gld: &Guild,
        rnd: &RoundId,
        number: u64,
    ) -> GuildRound {
        let mut g_rnd = GuildRound::default();
        let mut mention = format!("Match #{number}");
        if let Ok(role) = gld
            .create_role(cache, |r| {
                r.mentionable(true).name(format!("Match {}", number))
            })
            .await
        {
            mention = role.mention().to_string();
            let mut allowed_perms = Permissions::VIEW_CHANNEL;
            allowed_perms.insert(Permissions::CONNECT);
            allowed_perms.insert(Permissions::SEND_MESSAGES);
            allowed_perms.insert(Permissions::SPEAK);
            let overwrites = vec![PermissionOverwrite {
                allow: allowed_perms,
                deny: Permissions::empty(),
                kind: PermissionOverwriteType::Role(role.id),
            }];
            g_rnd.role = Some(role);
            if self.make_tc {
                if let Ok(tc) = gld
                    .create_channel(cache, |c| {
                        c.kind(ChannelType::Text)
                            .name(format!("Match {}", number))
                            .category(self.matches_category.id)
                            .permissions(overwrites.iter().cloned())
                    })
                    .await
                {
                    g_rnd.tc = Some(tc);
                }
            }
            if self.make_vc {
                if let Ok(vc) = gld
                    .create_channel(cache, |c| {
                        c.kind(ChannelType::Voice)
                            .name(format!("Match {}", number))
                            .category(self.matches_category.id)
                            .permissions(overwrites.into_iter())
                    })
                    .await
                {
                    g_rnd.vc = Some(vc);
                }
            }
        }
        g_rnd.message = self
            .pairings_channel
            .send_message(&cache, |m| {
                m.content(format!("{mention} you have been paired!"))
            })
            .await
            .ok();
        self.guild_rounds.insert(*rnd, g_rnd.clone());
        g_rnd
    }

    pub async fn clear_round_data(&mut self, rnd: &RoundId, http: &Http) {
        if let Some(g_rnd) = self.guild_rounds.remove(rnd) {
            g_rnd.delete_guild_data(http).await;
        }
    }

    pub fn get_user_id(&self, user: &PlayerId) -> Option<UserId> {
        self.players.get_left(user).cloned()
    }

    pub fn add_player(&mut self, name: String, user: UserId) -> Result<(), TournamentError> {
        if let OpData::RegisterPlayer(PlayerIdentifier::Id(id)) = self
            .tourn
            .apply_op(TournOp::RegisterGuest((*SQUIRE_ACCOUNT_ID).into(), name))?
        {
            self.players.insert(user, id);
        }
        Ok(())
    }

    pub fn add_guest(&mut self, name: String) -> Result<(), TournamentError> {
        let plyr_ident = self.tourn.apply_op(TournOp::RegisterGuest(
            (*SQUIRE_ACCOUNT_ID).into(),
            name.clone(),
        ))?;
        if let OpData::RegisterPlayer(PlayerIdentifier::Id(plyr_id)) = plyr_ident {
            self.guests.insert(name, plyr_id);
        }
        Ok(())
    }

    pub async fn spawn_status_message(
        &mut self,
        origin: &Message,
        cache: &impl CacheHttp,
    ) -> CommandResult {
        let status = origin.reply(cache, "\u{200b}").await?;
        self.tourn_status = Some(status);
        update_status_message(cache, self).await;
        Ok(())
    }
}

impl fmt::Display for RoundCreationFailure {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        use RoundCreationFailure::*;
        write!(
            f,
            "{}",
            match self {
                VC => "voice channel",
                TC => "text channel",
                Role => "role",
                Message => "match message",
            }
        )
    }
}

impl From<TournamentSetting> for SquireTournamentSetting {
    fn from(setting: TournamentSetting) -> Self {
        SquireTournamentSetting::TournamentSetting(setting)
    }
}

impl From<TournOp> for GuildTournamentAction {
    fn from(op: TournOp) -> Self {
        GuildTournamentAction::Operation(op)
    }
}
