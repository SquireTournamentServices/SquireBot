use core::fmt;
use std::collections::{HashMap, HashSet};
use std::hash::{Hash, Hasher};

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
use squire_core::{
    operations::{OpData, TournOp},
    player_registry::PlayerIdentifier,
    round_registry::RoundIdentifier,
    swiss_pairings::{PlayerId, TournamentError},
    tournament::{Tournament, TournamentId, TournamentPreset},
};

use crate::utils::embeds::update_status_message;

use super::timer_warnings::TimerWarnings;

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
    pub(crate) make_vc: bool,
    pub(crate) make_tc: bool,
    pub(crate) match_vcs: HashMap<RoundIdentifier, GuildChannel>,
    pub(crate) match_tcs: HashMap<RoundIdentifier, GuildChannel>,
    pub(crate) match_roles: HashMap<RoundIdentifier, Role>,
    pub(crate) match_timers: HashMap<RoundIdentifier, Message>,
    pub(crate) round_warnings: HashMap<RoundIdentifier, TimerWarnings>,
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
            match_roles: HashMap::new(),
            match_timers: HashMap::new(),
            round_warnings: HashMap::new(),
            standings_message: None,
            tourn: Tournament::from_preset(name, preset, format),
            update_standings: false,
            update_status: false,
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
        rnd: &RoundIdentifier,
        number: u64,
    ) -> Result<(), RoundCreationFailure> {
        let role = gld
            .create_role(cache, |r| {
                r.mentionable(true).name(format!("Match {}", number))
            })
            .await
            .map_err(|_| RoundCreationFailure::Role)?;
        let msg = self
            .pairings_channel
            .send_message(&cache, |m| {
                m.content(format!("{} you have been paired!", role.mention()))
            })
            .await
            .map_err(|_| RoundCreationFailure::Message)?;
        self.match_timers.insert(rnd.clone(), msg);
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
            let tc = gld
                .create_channel(cache, |c| {
                    c.kind(ChannelType::Text)
                        .name(format!("Match {}", number))
                        .category(self.matches_category.id)
                        .permissions(overwrites.iter().cloned())
                })
                .await
                .map_err(|_| RoundCreationFailure::TC)?;
            self.match_tcs.insert(rnd.clone(), tc);
        }
        if self.make_vc {
            let vc = gld
                .create_channel(cache, |c| {
                    c.kind(ChannelType::Voice)
                        .name(format!("Match {}", number))
                        .category(self.matches_category.id)
                        .permissions(overwrites.into_iter())
                })
                .await
                .map_err(|_| RoundCreationFailure::VC)?;
            self.match_vcs.insert(rnd.clone(), vc);
        }
        Ok(())
    }

    // NOTE: This will not delete roles. That is done at the end of the tournament
    pub async fn clear_round_data(&mut self, rnd: &RoundIdentifier, http: &Http) {
        if let Some(tc) = self.match_tcs.remove(rnd) {
            let _ = tc.delete(http).await;
        }
        if let Some(vc) = self.match_vcs.remove(rnd) {
            let _ = vc.delete(http).await;
        }
        self.match_timers.remove(rnd);
    }

    pub fn get_user_id(&self, user: &PlayerId) -> Option<UserId> {
        self.players.get_left(user).cloned()
    }

    pub fn add_player(&mut self, name: String, user: UserId) -> Result<(), TournamentError> {
        if let OpData::RegisterPlayer(PlayerIdentifier::Id(id)) =
            self.tourn.apply_op(TournOp::RegisterPlayer(name))?
        {
            self.players.insert(user, id);
        }
        Ok(())
    }

    pub async fn spawn_status_message(
        &mut self,
        origin: &Message,
        cache: &impl CacheHttp,
    ) -> CommandResult {
        let status = origin.reply(cache, "").await?;
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

impl Hash for GuildTournament {
    fn hash<H>(&self, state: &mut H)
    where
        H: Hasher,
    {
        let _ = &self.tourn.hash(state);
    }
}
