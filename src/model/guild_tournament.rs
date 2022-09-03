use std::{
    collections::{HashMap, HashSet},
    fmt,
    hash::{Hash, Hasher},
};

use dashmap::{DashMap, DashSet};
use serde::{Deserialize, Serialize};

use serenity::{
    client::Cache,
    framework::standard::CommandResult,
    http::{CacheHttp, Http},
    model::channel::ChannelCategory,
    CacheAndHttp,
    {
        model::{
            channel::{
                Channel, ChannelType, GuildChannel, Message, PermissionOverwrite,
                PermissionOverwriteType,
            },
            guild::{Guild, Role},
            id::{ChannelId, GuildId, MessageId, RoleId, UserId},
            Permissions,
        },
        prelude::*,
    },
};

use cycle_map::CycleMap;
use squire_lib::{
    identifiers::{PlayerIdentifier, AdminId, PlayerId, RoundIdentifier},
    operations::{OpData, TournOp},
    admin::Admin,
    error::TournamentError,
    tournament::{Tournament, TournamentId, TournamentPreset}, round::RoundId,
};

use crate::{
    utils::embeds::update_status_message,
    model::{
        timer_warnings::TimerWarnings,
        consts::SQUIRE_ACCOUNT_ID,
    },
};

pub enum RoundCreationFailure {
    VC,
    TC,
    Role,
    Message,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GuildTournament {
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
    pub(crate) match_vcs: HashMap<RoundId, GuildChannel>,
    pub(crate) match_tcs: HashMap<RoundId, GuildChannel>,
    pub(crate) match_roles: HashMap<RoundId, Role>,
    pub(crate) match_timers: HashMap<RoundId, Message>,
    pub(crate) round_warnings: HashMap<RoundId, TimerWarnings>,
    pub(crate) standings_message: Option<Message>,
    pub(crate) tourn: Tournament,
    pub(crate) update_standings: bool,
    pub(crate) update_status: bool,
    pub(crate) guild_id: GuildId,
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
        let admin = Admin { id: (*SQUIRE_ACCOUNT_ID).into(), name: "Squire Bot".into() };
        tourn.admins.insert((*SQUIRE_ACCOUNT_ID).into(), admin);
        Self {
            guild_id,
            tourn_role,
            judge_role,
            tourn_admin_role,
            pairings_channel,
            matches_category,
            make_vc,
            match_vcs: HashMap::new(),
            make_tc,
            match_tcs: HashMap::new(),
            tourn_status: None,
            players: CycleMap::new(),
            guests: CycleMap::new(),
            match_roles: HashMap::new(),
            match_timers: HashMap::new(),
            round_warnings: HashMap::new(),
            standings_message: None,
            tourn,
            update_standings: true,
            update_status: true,
        }
    }

    pub fn get_id(&self) -> TournamentId {
        self.tourn.id.clone()
    }

    pub fn get_player_id(&self, user: &UserId) -> Option<PlayerId> {
        self.players.get_right(user).cloned()
    }

    pub async fn create_round_data(
        &mut self,
        cache: &impl CacheHttp,
        gld: &Guild,
        rnd: &RoundId,
        number: u64,
    ) -> Result<(), RoundCreationFailure> {
        self.round_warnings.insert(*rnd, TimerWarnings::default());
        let mut mention = format!("Match #{number}");
        if let Ok(role) = gld
            .create_role(cache, |r| {
                r.mentionable(true).name(format!("Match {}", number))
            })
            .await {
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
                self.match_roles.insert(rnd.clone(), role);
                if self.make_tc {
                    if let Ok(tc) = gld
                        .create_channel(cache, |c| {
                            c.kind(ChannelType::Text)
                                .name(format!("Match {}", number))
                                .category(self.matches_category.id)
                                .permissions(overwrites.iter().cloned())
                        })
                        .await {
                        self.match_tcs.insert(rnd.clone(), tc);
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
                        .await {
                        self.match_vcs.insert(rnd.clone(), vc);
                    }
                }
        }
        let msg = self
            .pairings_channel
            .send_message(&cache, |m| {
                m.content(format!("{mention} you have been paired!"))
            })
            .await
            .map_err(|_| RoundCreationFailure::Message)?;
        self.match_timers.insert(rnd.clone(), msg);
        Ok(())
    }

    // NOTE: This will not delete roles. That is done at the end of the tournament
    pub async fn clear_round_data(&mut self, rnd: &RoundId, http: &Http) {
        if let Some(tc) = self.match_tcs.remove(rnd) {
            let _ = tc.delete(http).await;
        }
        if let Some(vc) = self.match_vcs.remove(rnd) {
            let _ = vc.delete(http).await;
        }
        if let Some(mut role) = self.match_roles.remove(rnd) {
            let _ = role.delete(http).await;
        }
        self.match_timers.remove(rnd);
        self.round_warnings.remove(rnd);
    }

    pub fn get_user_id(&self, user: &PlayerId) -> Option<UserId> {
        self.players.get_left(user).cloned()
    }

    pub fn add_player(&mut self, name: String, user: UserId) -> Result<(), TournamentError> {
        if let OpData::RegisterPlayer(PlayerIdentifier::Id(id)) =
            self.tourn.apply_op(TournOp::RegisterGuest((*SQUIRE_ACCOUNT_ID).into(), name))?
        {
            self.players.insert(user, id);
        }
        Ok(())
    }

    pub fn add_guest(&mut self, name: String) -> Result<(), TournamentError> {
        let plyr_ident = self.tourn.apply_op(TournOp::RegisterGuest((*SQUIRE_ACCOUNT_ID).into(), name.clone()))?;
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
