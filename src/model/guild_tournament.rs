use std::{collections::HashMap, io::Write, time::Duration};

use itertools::Itertools;
use serde::{Deserialize, Serialize};
use tempfile::tempfile;

use serenity::{
    framework::standard::CommandResult,
    http::{CacheHttp, Http},
    model::channel::ChannelCategory,
    model::{
        channel::{
            AttachmentType, Channel, ChannelType, GuildChannel, Message, PermissionOverwrite,
            PermissionOverwriteType,
        },
        guild::{Guild, Role},
        id::{GuildId, RoleId, UserId},
        Permissions,
    },
    prelude::*,
};

use cycle_map::{CycleMap, GroupMap};

use squire_lib::{
    admin::Admin,
    identifiers::{PlayerId, PlayerIdentifier, RoundIdentifier},
    operations::{OpData, OpResult, TournOp},
    player::PlayerStatus,
    round::{RoundId, RoundResult, RoundStatus},
    settings::TournamentSetting,
    tournament::{Tournament, TournamentPreset},
};

use crate::{
    match_manager::{MatchUpdate, MatchUpdateMessage},
    model::{
        confirmation::{
            CancelTournamentConfirmation, CutToTopConfirmation, EndTournamentConfirmation,
            PairRoundConfirmation, PruneDecksConfirmation, PrunePlayersConfirmation,
        },
        consts::SQUIRE_ACCOUNT_ID,
        containers::{ConfirmationsContainer, MatchUpdateSenderContainer},
        guild_rounds::{GuildRound, GuildRoundData, TimerWarnings, TrackingRound},
    },
    utils::{
        default_response::{error_to_content, op_to_content},
        embeds::{player_embed_info, safe_embeds, standings_embeds, tournament_embed_info},
        id_resolver::user_id_resolver,
        sort_deck::TypeSortedDeck,
    },
};

#[allow(clippy::large_enum_variant)]
#[derive(Serialize, Deserialize, Debug, Clone)]
pub enum SquireTournamentSetting {
    PairingsChannel(GuildChannel),
    MatchesCategory(ChannelCategory),
    CreateVC(bool),
    CreateTC(bool),
    TournamentSetting(TournamentSetting),
}

#[allow(clippy::large_enum_variant)]
pub enum GuildTournamentAction {
    // Actions to query information
    GetRawStandings(usize),
    ViewDecklist(PlayerIdentifier, String),
    ViewPlayerDecks(PlayerIdentifier),
    ViewPlayerProfile(PlayerIdentifier),
    ViewAllPlayers,
    CreateStandings,
    CreateTournamentStatus,
    ViewMatchStatus(RoundIdentifier),
    // Wrappers for tournament operations
    RemoveMatch(RoundIdentifier),
    PrunePlayers,
    PruneDecks,
    End,
    Cancel,
    Cut(usize),
    RecordResult(PlayerIdentifier, RoundResult),
    ConfirmResult(PlayerIdentifier),
    AdminRecordResult(RoundIdentifier, RoundResult),
    AdminConfirmResult(RoundIdentifier, PlayerIdentifier),
    GiveBye(PlayerIdentifier),
    RegisterPlayer(UserId),
    AdminRegisterPlayer(UserId),
    RegisterGuest(String),
    DropPlayer(PlayerIdentifier),
    CreateMatch(Vec<String>),
    PairRound,
    TimeExtension(RoundIdentifier, Duration),
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
    pub(crate) guild_rounds: HashMap<RoundId, GuildRoundData>,
    pub(crate) standings_message: Option<Message>,
}

#[allow(clippy::too_many_arguments)]
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
            id: *SQUIRE_ACCOUNT_ID,
            name: "Squire Bot".into(),
        };
        tourn.admins.insert(*SQUIRE_ACCOUNT_ID, admin);
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

    pub fn get_player_id(&self, user: &UserId) -> Option<PlayerId> {
        self.players.get_right(user).cloned()
    }

    pub fn get_guild_round(&self, r_id: &RoundId) -> Option<GuildRound> {
        let round = self.tourn.get_round(&(*r_id).into()).ok()?;
        let g_rnd = self.guild_rounds.get(r_id).cloned()?;
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
        let vc_mention = g_rnd.vc.map(|vc| vc.mention().to_string());
        let tc_mention = g_rnd.tc.map(|tc| tc.mention().to_string());
        let role_mention = g_rnd.role.map(|role| role.mention().to_string());
        Some(GuildRound {
            round,
            players,
            vc_mention,
            tc_mention,
            role_mention,
            warnings: TimerWarnings::default(),
            use_table_number: self.tourn.use_table_number,
        })
    }

    pub fn get_tracking_round(&self, r_id: &RoundId) -> Option<TrackingRound> {
        let message = self
            .guild_rounds
            .get(r_id)
            .and_then(|r| r.message.clone())?;
        self.get_guild_round(r_id)
            .map(|round| TrackingRound { round, message })
    }

    pub async fn create_round_data(
        &mut self,
        cache: &impl CacheHttp,
        gld: &Guild,
        rnd: &RoundId,
        number: u64,
    ) {
        let mut g_rnd = GuildRoundData::default();
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
        self.guild_rounds.insert(*rnd, g_rnd);
    }

    pub async fn clear_round_data(&mut self, rnd: &RoundId, http: &Http) {
        if let Some(g_rnd) = self.guild_rounds.remove(rnd) {
            g_rnd.delete_guild_data(http).await;
        }
    }

    pub fn get_user_id(&self, plyr: &PlayerId) -> Option<UserId> {
        self.players.get_left(plyr).cloned()
    }

    /// Resolves a player's name from their player ident
    pub fn resolve_player_name(&self, id: &PlayerId) -> Option<String> {
        self.players
            .get_left(id)
            .map(|u_id| u_id.mention().to_string())
            .or_else(|| self.guests.get_left(id).cloned())
    }

    /// Remove all tournament data from the guild
    pub async fn purge(&mut self, ctx: &Context) {
        let data = ctx.data.read().await;
        let sender = data.get::<MatchUpdateSenderContainer>().unwrap();
        for rnd in self.tourn.round_reg.rounds.values() {
            let _ = sender.send(MatchUpdateMessage {
                id: rnd.id,
                update: MatchUpdate::MatchCancelled,
            });
            if let Some(gr) = self.guild_rounds.get_mut(&rnd.id) {
                if let Some(role) = &mut gr.role {
                    let _ = role.delete(&ctx.http).await;
                    gr.role = None;
                }
                if let Some(vc) = &mut gr.vc {
                    let _ = vc.delete(&ctx.http).await;
                    gr.vc = None;
                }
                if let Some(tc) = &mut gr.tc {
                    let _ = tc.delete(&ctx.http).await;
                    gr.tc = None;
                }
            }
        }
        let _ = self.tourn_role.delete(&ctx.http).await;
    }

    /// Remove all tournament data from the guild and end the tournament
    pub async fn end(&mut self, ctx: &Context) -> OpResult {
        let result = self.tourn.apply_op(TournOp::End(*SQUIRE_ACCOUNT_ID));
        if result.is_ok() {
            self.purge(ctx).await;
        }
        result
    }

    /// Remove all tournament data from the guild and cancel the tournament
    pub async fn cancel(&mut self, ctx: &Context) -> OpResult {
        let result = self.tourn.apply_op(TournOp::Cancel(*SQUIRE_ACCOUNT_ID));
        if result.is_ok() {
            self.purge(ctx).await;
        }
        result
    }

    /// Updates the standings embed
    pub async fn update_standings(&mut self, ctx: &Context) {
        if self.standings_message.is_some() {
            let standings = self.tourn.get_standings();
            let embeds = standings_embeds(standings, self);
            let msg = self.standings_message.as_mut().unwrap();
            let _ = msg.edit(&ctx.http, |m| m.add_embeds(embeds)).await;
        }
    }

    /// Updates the status embed
    pub async fn update_status(&mut self, ctx: &Context) {
        if self.tourn_status.is_some() {
            let fields = tournament_embed_info(self);
            let msg = self.tourn_status.as_mut().unwrap();
            let _ = msg
                .edit(&ctx.http, |m| {
                    m.add_embeds(safe_embeds(format!("{} Status:", self.tourn.name), fields))
                })
                .await;
        }
    }

    pub async fn take_action(
        &mut self,
        ctx: &Context,
        msg: &Message,
        action: GuildTournamentAction,
    ) -> CommandResult {
        use GuildTournamentAction::*;
        match action {
            TimeExtension(rnd, dur) => {
                let opt_id = self.tourn.round_reg.get_round_id(&rnd);
                let content = match self.tourn.apply_op(TournOp::TimeExtension(
                    (*SQUIRE_ACCOUNT_ID).into(),
                    rnd,
                    dur,
                )) {
                    Err(err) => error_to_content(err),
                    Ok(_) => {
                        let _ = ctx
                            .data
                            .read()
                            .await
                            .get::<MatchUpdateSenderContainer>()
                            .unwrap()
                            .send(MatchUpdateMessage {
                                id: opt_id.unwrap(),
                                update: MatchUpdate::TimeExtention(dur),
                            });
                        "Match successfully removed."
                    }
                };
                msg.reply(&ctx.http, content).await?;
            }
            Cut(len) => {
                let confirm = CutToTopConfirmation {
                    tourn_id: self.tourn.id,
                    len,
                };
                ctx.data
                    .read()
                    .await
                    .get::<ConfirmationsContainer>()
                    .unwrap()
                    .insert(msg.author.id, Box::new(confirm));
                msg.reply(&ctx.http, format!("You are about to cut the tournament to the top {len} players. Are you sure you want to? (!yes or !no)")).await?;
            }
            PairRound => {
                let confirm = PairRoundConfirmation {
                    tourn_id: self.tourn.id,
                };
                ctx.data
                    .read()
                    .await
                    .get::<ConfirmationsContainer>()
                    .unwrap()
                    .insert(msg.author.id, Box::new(confirm));
                msg.reply(&ctx.http, "You are about to pair the next round of the tournament. Are you sure you want to? (!yes or !no)").await?;
                self.update_status(ctx).await;
            }
            RemoveMatch(r_ident) => {
                let r_id = match self.tourn.round_reg.get_round_id(&r_ident) {
                    Ok(id) => id,
                    Err(err) => {
                        msg.reply(&ctx.http, error_to_content(err)).await?;
                        return Ok(());
                    }
                };
                let update = MatchUpdateMessage {
                    id: r_id,
                    update: MatchUpdate::MatchCancelled,
                };
                let _ = ctx
                    .data
                    .read()
                    .await
                    .get::<MatchUpdateSenderContainer>()
                    .unwrap()
                    .send(update);
                self.clear_round_data(&r_id, &ctx.http).await;
                let content = match self
                    .tourn
                    .apply_op(TournOp::RemoveRound(*SQUIRE_ACCOUNT_ID, r_id.into()))
                {
                    Ok(_) => "Match successfully removed.",
                    Err(err) => error_to_content(err),
                };
                msg.reply(&ctx.http, content).await?;
                self.update_status(ctx).await;
                self.update_standings(ctx).await;
            }
            RecordResult(p_ident, result) => {
                let opt_p_id = self.tourn.player_reg.get_player_id(&p_ident);
                let op = TournOp::RecordResult(p_ident, result.clone());
                match self.tourn.apply_op(op) {
                    Err(err) => {
                        msg.reply(&ctx.http, error_to_content(err)).await?;
                    }
                    Ok(_) => {
                        let p_id = opt_p_id.unwrap();
                        let r_id = self
                            .tourn
                            .round_reg
                            .get_player_active_round(&p_id)
                            .unwrap()
                            .id;
                        let update = MatchUpdateMessage {
                            id: r_id,
                            update: MatchUpdate::RecordResult(result),
                        };
                        let _ = ctx
                            .data
                            .read()
                            .await
                            .get::<MatchUpdateSenderContainer>()
                            .unwrap()
                            .send(update);
                        let mut resp = msg
                            .reply(
                                &ctx.http,
                                "Result recorded!! The current status of our round is:",
                            )
                            .await?;
                        if let Some(gr) = self.get_guild_round(&r_id) {
                            let (title, fields) = gr.embed_info();
                            resp.edit(&ctx.http, |m| m.add_embeds(safe_embeds(title, fields)))
                                .await?;
                        }
                    }
                }
            }
            ConfirmResult(p_ident) => {
                let opt_p_id = self.tourn.player_reg.get_player_id(&p_ident);
                let op = TournOp::ConfirmResult(p_ident);
                match self.tourn.apply_op(op) {
                    Err(err) => {
                        msg.reply(&ctx.http, error_to_content(err)).await?;
                    }
                    Ok(OpData::ConfirmResult(_, status)) => {
                        let p_id = opt_p_id.unwrap();
                        let r_id = self
                            .tourn
                            .round_reg
                            .get_player_active_round(&p_id)
                            .unwrap()
                            .id;
                        let update = MatchUpdateMessage {
                            id: r_id,
                            update: MatchUpdate::RecordConfirmation(p_id),
                        };
                        let _ = ctx
                            .data
                            .read()
                            .await
                            .get::<MatchUpdateSenderContainer>()
                            .unwrap()
                            .send(update);
                        let mut resp = msg
                            .reply(
                                &ctx.http,
                                "Confirmation recorded!! The current status of our round is:",
                            )
                            .await?;
                        if let Some(tr) = self.get_tracking_round(&r_id) {
                            let (title, fields) = tr.embed_info();
                            resp.edit(&ctx.http, |m| m.add_embeds(safe_embeds(title, fields)))
                                .await?;
                        }
                        if status == RoundStatus::Certified {
                            self.update_status(ctx).await;
                            self.update_standings(ctx).await;
                        }
                    }
                    _ => {
                        unreachable!(
                            "Recording the result of a round returns and `Err` or `Ok(OpData::ConfirmResult)`)"
                        );
                    }
                }
            }
            AdminRecordResult(r_ident, result) => {
                let opt_r_id = self.tourn.round_reg.get_round_id(&r_ident);
                let op = TournOp::AdminRecordResult(
                    (*SQUIRE_ACCOUNT_ID).into(),
                    r_ident,
                    result.clone(),
                );
                match self.tourn.apply_op(op) {
                    Err(err) => {
                        msg.reply(&ctx.http, error_to_content(err)).await?;
                    }
                    Ok(_) => {
                        let r_id = opt_r_id.unwrap();
                        let update = MatchUpdateMessage {
                            id: r_id,
                            update: MatchUpdate::RecordResult(result),
                        };
                        let _ = ctx
                            .data
                            .read()
                            .await
                            .get::<MatchUpdateSenderContainer>()
                            .unwrap()
                            .send(update);
                        let mut resp = msg
                            .reply(
                                &ctx.http,
                                "Result recorded!! The current status of the round is:",
                            )
                            .await?;
                        if let Some(tr) = self.get_tracking_round(&r_id) {
                            let (title, fields) = tr.embed_info();
                            resp.edit(&ctx.http, |m| m.add_embeds(safe_embeds(title, fields)))
                                .await?;
                        }
                    }
                }
            }
            AdminConfirmResult(r_ident, p_ident) => {
                let opt_r_id = self.tourn.round_reg.get_round_id(&r_ident);
                let opt_p_id = self.tourn.player_reg.get_player_id(&p_ident);
                let op = TournOp::AdminConfirmResult((*SQUIRE_ACCOUNT_ID).into(), r_ident, p_ident);
                match self.tourn.apply_op(op) {
                    Err(err) => {
                        msg.reply(&ctx.http, error_to_content(err)).await?;
                    }
                    Ok(OpData::ConfirmResult(_, status)) => {
                        let p_id = opt_p_id.unwrap();
                        let r_id = opt_r_id.unwrap();
                        let update = MatchUpdateMessage {
                            id: r_id,
                            update: MatchUpdate::RecordConfirmation(p_id),
                        };
                        let _ = ctx
                            .data
                            .read()
                            .await
                            .get::<MatchUpdateSenderContainer>()
                            .unwrap()
                            .send(update);
                        let mut resp = msg
                            .reply(
                                &ctx.http,
                                "Result recorded!! The current status of the round is:",
                            )
                            .await?;
                        if let Some(tr) = self.get_tracking_round(&r_id) {
                            let (title, fields) = tr.embed_info();
                            resp.edit(&ctx.http, |m| m.add_embeds(safe_embeds(title, fields)))
                                .await?;
                        }
                        if status == RoundStatus::Certified {
                            self.update_status(ctx).await;
                            self.update_standings(ctx).await;
                        }
                    }
                    _ => {
                        unreachable!(
                            "Recording the result of a round returns and `Err` or `Ok(OpData::ConfirmResult)`)"
                        );
                    }
                }
            }
            DropPlayer(p_ident) => {
                let opt_id = self.tourn.player_reg.get_player_id(&p_ident);
                let op = TournOp::AdminDropPlayer(*SQUIRE_ACCOUNT_ID, p_ident.clone());
                match self.tourn.apply_op(op) {
                    Err(err) => {
                        msg.reply(&ctx.http, error_to_content(err)).await?;
                    }
                    Ok(_) => {
                        let id = self.tourn.player_reg.get_player_id(&p_ident).unwrap();
                        let data = ctx.data.read().await;
                        let sender = data.get::<MatchUpdateSenderContainer>().unwrap();
                        for rnd in self.tourn.get_player_rounds(&p_ident).unwrap() {
                            let _ = sender.send(MatchUpdateMessage {
                                id: rnd.id,
                                update: MatchUpdate::DropPlayer(id),
                            });
                        }
                        self.update_status(ctx).await;
                        self.update_standings(ctx).await;
                        if let Some(u_id) = self.get_user_id(&opt_id.unwrap()) {
                            msg.guild(ctx)
                                .unwrap()
                                .member(ctx, u_id)
                                .await
                                .unwrap()
                                .remove_role(ctx, self.tourn_role.id)
                                .await?;
                        }
                    }
                }
            }
            PruneDecks => {
                let confirm = PruneDecksConfirmation {
                    tourn_id: self.tourn.id,
                };
                ctx.data
                    .read()
                    .await
                    .get::<ConfirmationsContainer>()
                    .unwrap()
                    .insert(msg.author.id, Box::new(confirm));
                let content = if self.tourn.require_deck_reg {
                    let max = self.tourn.max_deck_count;
                    format!("Prune players' decks. After this, every player will have at most {max} decks. Are you sure you want to? (!yes or !no)")
                } else {
                    "That tournament doesn't require deck registration. Pruning will do nothing."
                        .to_string()
                };
                msg.reply(&ctx.http, content).await?;
            }
            PrunePlayers => {
                let confirm = PrunePlayersConfirmation {
                    tourn_id: self.tourn.id,
                };
                ctx.data
                    .read()
                    .await
                    .get::<ConfirmationsContainer>()
                    .unwrap()
                    .insert(msg.author.id, Box::new(confirm));
                let min = self.tourn.min_deck_count;
                let (decks, checkin) = self.tourn.count_to_prune_players();
                let content = match (self.tourn.require_deck_reg, self.tourn.require_check_in) {
                    (true, true) => {
                        format!("You are about to prune {decks} players because they didn't register at least {min} decks and {checkin} players because they didn't check in. Are you sure you want to? (!yes or !no)")
                    },
                    (true, false) => {
                        format!("You are about to prune {decks} players because they didn't register at least {min} decks. Are you sure you want to? (!yes or !no)")
                    },
                    (false, true) => {
                        format!("You are about to prune {checkin} players because they didn't check in. Are you sure you want to? (!yes or !no)")
                    },
                    (false, false) => {
                        "That tournament doesn't require deck registration nor player check in, so pruning players will do nothing.".to_string()
                    },
                };
                msg.reply(
                    &ctx.http,
                    format!("{content} Are you sure you want to? (!yes or !no)"),
                )
                .await?;
            }
            End => {
                let confirm = EndTournamentConfirmation {
                    tourn_id: self.tourn.id,
                };
                ctx.data
                    .read()
                    .await
                    .get::<ConfirmationsContainer>()
                    .unwrap()
                    .insert(msg.author.id, Box::new(confirm));
                msg.reply(
                    &ctx.http,
                    "You are about to end the tournament. Are you sure you want to? (!yes or !no)"
                        .to_string(),
                )
                .await?;
            }
            Cancel => {
                let confirm = CancelTournamentConfirmation {
                    tourn_id: self.tourn.id,
                };
                ctx.data
                    .read()
                    .await
                    .get::<ConfirmationsContainer>()
                    .unwrap()
                    .insert(msg.author.id, Box::new(confirm));
                msg.reply(&ctx.http, "You are about to cancel the tournament. Are you sure you want to? (!yes or !no)".to_string()).await?;
            }
            GiveBye(p_ident) => {
                let opt_id = self.tourn.player_reg.get_player_id(&p_ident);
                let op = TournOp::GiveBye(*SQUIRE_ACCOUNT_ID, p_ident);
                match self.tourn.apply_op(op) {
                    Err(err) => {
                        msg.reply(&ctx.http, error_to_content(err)).await?;
                    }
                    Ok(_) => {
                        self.update_status(ctx).await;
                        self.update_standings(ctx).await;
                        let id = opt_id.unwrap();
                        let mention = self
                            .players
                            .get_left(&id)
                            .map(|id| id.mention().to_string())
                            .unwrap_or_else(|| self.guests.get_left(&id).unwrap().clone());
                        self.pairings_channel
                            .send_message(&ctx.http, |m| {
                                m.content(format!("{mention}, you have been given a bye!"))
                            })
                            .await?;
                    }
                }
            }
            GetRawStandings(count) => {
                let standings = self.tourn.get_standings();
                let mut output = tempfile().unwrap();
                for (i, (id, _)) in standings.scores.iter().enumerate().take(count) {
                    let _ = writeln!(output, "{i}) {}", self.resolve_player_name(id).unwrap());
                }
                let to_send = tokio::fs::File::from_std(output);
                match msg.channel(&ctx.http).await? {
                    Channel::Guild(c) => {
                        c.send_message(&ctx.http, |m| {
                            m.content("Here you go!!").files(
                                [AttachmentType::File {
                                    file: &to_send,
                                    filename: String::from("standings.txt"),
                                }]
                                .into_iter(),
                            )
                        })
                        .await?;
                    }
                    _ => {
                        unreachable!("How did you get here?");
                    }
                }
            }
            ViewAllPlayers => {
                let mut resp = msg.reply(&ctx.http, "Here are all the players!!").await?;
                let players: GroupMap<String, PlayerStatus> = self
                    .tourn
                    .player_reg
                    .players
                    .iter()
                    .map(|(id, plyr)| (self.resolve_player_name(id).unwrap(), plyr.status))
                    .collect();
                resp.edit(&ctx.http, |m| {
                    m.embed(|e| {
                        e.fields(players.iter_right().map(|s| {
                            let mut iter = players.get_left_iter(s).unwrap();
                            (format!("{s}: {}", iter.len()), iter.join(" "), true)
                        }))
                    })
                })
                .await?;
            }
            CreateStandings => {
                let resp = msg.reply(&ctx.http, "\u{200b}").await?;
                self.standings_message = Some(resp);
                self.update_standings(ctx).await;
            }
            ViewDecklist(p_ident, deck_name) => {
                let plyr_id = match self.tourn.player_reg.get_player_id(&p_ident) {
                    Ok(id) => id,
                    Err(err) => {
                        msg.reply(&ctx.http, error_to_content(err)).await?;
                        return Ok(());
                    }
                };
                let deck = match self.tourn.get_player_deck(&p_ident, &deck_name) {
                    Ok(deck) => deck,
                    Err(err) => {
                        msg.reply(&ctx.http, error_to_content(err)).await?;
                        return Ok(());
                    }
                };
                let title = format!("{}'s deck", self.get_player_mention(&plyr_id).unwrap());
                let sorted_deck = TypeSortedDeck::from(deck);
                let fields = sorted_deck.embed_fields();
                let mut resp = msg.reply(&ctx.http, "Here you go!").await?;
                resp.edit(&ctx.http, |m| m.add_embeds(safe_embeds(title, fields)))
                    .await?;
            }
            ViewPlayerDecks(p_ident) => {
                let plyr = match self.tourn.get_player(&p_ident) {
                    Ok(plyr) => plyr,
                    Err(err) => {
                        msg.reply(&ctx.http, error_to_content(err)).await?;
                        return Ok(());
                    }
                };
                if plyr.decks.is_empty() {
                    msg.reply(&ctx.http, "That player has no decks.").await?;
                    return Ok(());
                }
                for (name, deck) in plyr.decks {
                    let sorted_deck = TypeSortedDeck::from(deck);
                    let fields = sorted_deck.embed_fields();
                    let mut resp = msg.reply(&ctx.http, "Here you go!").await?;
                    resp.edit(&ctx.http, |m| m.add_embeds(safe_embeds(name, fields)))
                        .await?;
                }
            }
            ViewPlayerProfile(p_ident) => {
                let plyr_id = match self.tourn.player_reg.get_player_id(&p_ident) {
                    Ok(id) => id,
                    Err(err) => {
                        msg.reply(&ctx.http, error_to_content(err)).await?;
                        return Ok(());
                    }
                };
                let mention = self.get_player_mention(&plyr_id).unwrap();
                let fields = player_embed_info(plyr_id, self);
                let mut resp = msg.reply(&ctx.http, "Here you go!").await?;
                resp.edit(&ctx.http, |m| {
                    m.add_embeds(safe_embeds(format!("{mention}'s Profile"), fields))
                })
                .await?;
            }
            ViewMatchStatus(r_ident) => {
                let r_id = match self.tourn.round_reg.get_round_id(&r_ident) {
                    Ok(id) => id,
                    Err(err) => {
                        msg.reply(&ctx.http, error_to_content(err)).await?;
                        return Ok(());
                    }
                };
                let gr = self.get_guild_round(&r_id).unwrap();
                let (title, fields) = gr.embed_info();
                let mut resp = msg.reply(&ctx.http, "Here you go!").await?;
                resp.edit(&ctx.http, |m| m.add_embeds(safe_embeds(title, fields)))
                    .await?;
            }
            CreateTournamentStatus => {
                let resp = msg.reply(&ctx.http, "\u{200b}").await?;
                self.tourn_status = Some(resp);
                self.update_status(ctx).await;
            }
            RegisterPlayer(user_id) => {
                let content = match self.tourn.apply_op(TournOp::RegisterGuest(
                    (*SQUIRE_ACCOUNT_ID).into(),
                    user_id.to_string(),
                )) {
                    Ok(id) => {
                        if let OpData::RegisterPlayer(ident) = id {
                            let id = self.tourn.player_reg.get_player_id(&ident).unwrap();
                            self.players.insert(user_id, id);
                        }
                        self.update_status(ctx).await;
                        "You have been successfully registered!!"
                    }
                    Err(err) => error_to_content(err),
                };
                msg.reply(&ctx.http, content).await?;
                msg.guild(ctx)
                    .unwrap()
                    .member(ctx, user_id)
                    .await
                    .unwrap()
                    .remove_role(ctx, self.tourn_role.id)
                    .await?;
            }
            AdminRegisterPlayer(user_id) => {
                let content = match self.tourn.apply_op(TournOp::RegisterGuest(
                    (*SQUIRE_ACCOUNT_ID).into(),
                    user_id.to_string(),
                )) {
                    Ok(id) => {
                        if let OpData::RegisterPlayer(ident) = id {
                            let id = self.tourn.player_reg.get_player_id(&ident).unwrap();
                            self.players.insert(user_id, id);
                        }
                        self.update_status(ctx).await;
                        "Player successfully registered!!"
                    }
                    Err(err) => error_to_content(err),
                };
                msg.reply(&ctx.http, content).await?;
                msg.guild(ctx)
                    .unwrap()
                    .member(ctx, user_id)
                    .await
                    .unwrap()
                    .remove_role(ctx, self.tourn_role.id)
                    .await?;
            }
            RegisterGuest(name) => {
                let content = match self.tourn.apply_op(TournOp::RegisterGuest(
                    (*SQUIRE_ACCOUNT_ID).into(),
                    name.clone(),
                )) {
                    Ok(id) => {
                        if let OpData::RegisterPlayer(ident) = id {
                            let id = self.tourn.player_reg.get_player_id(&ident).unwrap();
                            self.guests.insert(name, id);
                        }
                        self.update_status(ctx).await;
                        "Guest successfully registered!!"
                    }
                    Err(err) => error_to_content(err),
                };
                msg.reply(&ctx.http, content).await?;
            }
            CreateMatch(mut raw_plyrs) => {
                // If the last "player" has the same name as the tournament, we ignore it.
                if raw_plyrs
                    .last()
                    .map(|name| &self.tourn.name == name)
                    .unwrap_or_default()
                {
                    raw_plyrs.pop();
                }
                let mut plyr_ids = Vec::with_capacity(raw_plyrs.len());
                for name in raw_plyrs {
                    match user_id_resolver(ctx, msg, &name)
                        .await
                        .and_then(|id| self.players.get_right(&id))
                        .or_else(|| self.guests.get_right(&name))
                    {
                        Some(id) => {
                            plyr_ids.push((*id).into());
                        }
                        None => {
                            msg.reply(
                                &ctx.http,
                                format!("'{name}' is not registered for that tournament."),
                            )
                            .await?;
                            return Ok(());
                        }
                    }
                }
                match self
                    .tourn
                    .apply_op(TournOp::CreateRound(*SQUIRE_ACCOUNT_ID, plyr_ids))
                {
                    Ok(OpData::CreateRound(rnd_ident)) => {
                        let rnd = self.tourn.get_round(&rnd_ident).unwrap();
                        self.create_round_data(
                            &ctx,
                            &msg.guild(ctx).unwrap(),
                            &rnd.id,
                            rnd.match_number,
                        )
                        .await;
                        if let Some(tr) = self.get_tracking_round(&rnd.id) {
                            let message = MatchUpdateMessage {
                                id: rnd.id,
                                update: MatchUpdate::NewMatch(tr),
                            };
                            let _ = ctx
                                .data
                                .read()
                                .await
                                .get::<MatchUpdateSenderContainer>()
                                .unwrap()
                                .send(message);
                        }
                        self.update_status(ctx).await;
                        let mut resp = msg.reply(&ctx.http, "Match successfully created!!").await?;
                        if let Some(gr) = self.get_guild_round(&rnd.id) {
                            let (title, fields) = gr.embed_info();
                            resp.edit(&ctx.http, |m| m.add_embeds(safe_embeds(title, fields)))
                                .await?;
                        }
                    }
                    Err(err) => {
                        msg.reply(&ctx.http, error_to_content(err)).await?;
                    }
                    _ => {
                        unreachable!(
                            "Creating a round returns and `Err` or `Ok(OpData::CreateRound)`)"
                        );
                    }
                }
            }
            Operation(op) => {
                let mut content = op_to_content(&op);
                if let Err(err) = self.tourn.apply_op(op) {
                    content = error_to_content(err);
                };
                let _ = msg.reply(&ctx.http, content).await;
            }
        }
        Ok(())
    }

    pub fn get_player_mention(&self, plyr_id: &PlayerId) -> Option<String> {
        self.get_user_id(plyr_id)
            .map(|id| id.mention().to_string())
            .or_else(|| self.guests.get_left(&plyr_id).cloned())
    }
}

impl From<TournamentSetting> for SquireTournamentSetting {
    fn from(setting: TournamentSetting) -> Self {
        SquireTournamentSetting::TournamentSetting(setting)
    }
}
