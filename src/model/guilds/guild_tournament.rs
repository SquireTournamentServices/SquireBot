use std::{collections::HashMap, error::Error, io::Write, sync::Arc, time::Duration};

use chrono::Utc;
use itertools::Itertools;
use serde::{Deserialize, Serialize};
use tempfile::tempfile;

use serenity::{
    builder::CreateEmbed,
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

use cycle_map::{CycleMap, GroupMap};

use squire_lib::{
    admin::Admin,
    identifiers::{PlayerId, PlayerIdentifier, RoundIdentifier},
    operations::{AdminOp::*, JudgeOp::*, OpData, OpResult, PlayerOp::*, TournOp},
    players::PlayerStatus,
    rounds::{RoundId, RoundResult, RoundStatus},
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
        guilds::{GuildRound, GuildRoundData, TimerWarnings, TrackingRound},
        MessageContent,
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

pub enum GuildTournamentAction {
    // Actions to query information
    GetRawStandings(usize),
    ViewDecklist(PlayerIdentifier, String),
    ViewPlayerDecks(PlayerIdentifier),
    ViewPlayerProfile(PlayerIdentifier),
    ViewAllPlayers,
    CreateStandings(Arc<GuildChannel>),
    CreateTournamentStatus(Arc<GuildChannel>),
    ViewMatchStatus(RoundIdentifier),
    DeckCheck(RoundIdentifier),
    DeckDump(usize),
    ExportTournament,
    // Wrappers for tournament operations
    RemoveMatch(RoundIdentifier),
    PrunePlayers(UserId),
    PruneDecks(UserId),
    End(UserId),
    Cancel(UserId),
    Cut(UserId, usize),
    RecordResult(PlayerIdentifier, RoundResult),
    ConfirmResult(PlayerIdentifier),
    ConfirmAll,
    AdminRecordResult(RoundIdentifier, RoundResult),
    AdminConfirmResult(RoundIdentifier, PlayerIdentifier),
    GiveBye(PlayerIdentifier),
    RegisterPlayer(UserId),
    ReRegisterPlayer(UserId),
    AdminRegisterPlayer(UserId),
    AdminReRegisterPlayer(UserId),
    RegisterGuest(String),
    DropPlayer(PlayerIdentifier),
    CreateMatch(Vec<String>),
    PairRound(UserId),
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
                self.tourn.apply_op(Utc::now(), TournOp::AdminOp(
                    *SQUIRE_ACCOUNT_ID,
                    UpdateTournSetting(setting),
                ))?;
            }
        };
        Ok(OpData::Nothing)
    }

    pub fn get_player_id(&self, user: &UserId) -> Option<PlayerId> {
        self.players.get_right(user).cloned()
    }

    pub fn get_guild_round(&self, r_id: &RoundId) -> Option<GuildRound> {
        let round = self.tourn.get_round(&(*r_id).into()).ok()?.clone();
        let g_rnd = self.guild_rounds.get(r_id).cloned();
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
        let vc_mention = g_rnd
            .as_ref()
            .map(|gr| gr.vc.as_ref().map(|vc| vc.mention().to_string()))
            .flatten();
        let tc_mention = g_rnd
            .as_ref()
            .map(|gr| gr.tc.as_ref().map(|tc| tc.mention().to_string()))
            .flatten();
        let role_mention = g_rnd
            .as_ref()
            .map(|gr| gr.role.as_ref().map(|role| role.mention().to_string()))
            .flatten();
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
        cache: &(impl CacheHttp + AsRef<Http>),
        gld: &Guild,
        rnd: &RoundId,
        number: u64,
    ) {
        let mut g_rnd = GuildRoundData::default();
        let mut mention = format!("Match #{number}");
        let round = self.tourn.get_round(&(*rnd).into()).unwrap();
        if round.is_bye() {
            let gr = GuildRoundData {
                message: None,
                vc: None,
                tc: None,
                role: None,
                warnings: TimerWarnings {
                    five_min: true,
                    one_min: true,
                    time_up: true,
                },
            };
            self.guild_rounds.insert(*rnd, gr);
            return ();
        }
        if let Ok(role) = gld
            .create_role(cache, |r| {
                r.mentionable(true).name(format!("Match {}", number))
            })
            .await
        {
            for p_id in &round.players {
                if let Some(u_id) = self.players.get_left(&p_id) {
                    if let Ok(mut member) = gld.member(cache, u_id).await {
                        let _ = member.add_role(cache, role.id).await;
                    }
                }
            }
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
        let result = self
            .tourn
            .apply_op(Utc::now(), TournOp::AdminOp(*SQUIRE_ACCOUNT_ID, End));
        if result.is_ok() {
            self.purge(ctx).await;
        }
        result
    }

    /// Remove all tournament data from the guild and cancel the tournament
    pub async fn cancel(&mut self, ctx: &Context) -> OpResult {
        let result = self
            .tourn
            .apply_op(Utc::now(), TournOp::AdminOp(*SQUIRE_ACCOUNT_ID, Cancel));
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
            let _ = msg.edit(&ctx.http, |m| m.set_embeds(embeds)).await;
        }
    }

    /// Updates the status embed
    pub async fn update_status(&mut self, ctx: &Context) {
        if self.tourn_status.is_some() {
            let fields = tournament_embed_info(self);
            let msg = self.tourn_status.as_mut().unwrap();
            let _ = msg
                .edit(&ctx.http, |m| {
                    m.set_embeds(safe_embeds(format!("{} Status:", self.tourn.name), fields))
                })
                .await;
        }
    }

    pub async fn take_action(
        &mut self,
        ctx: &Context,
        action: GuildTournamentAction,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        use GuildTournamentAction::*;
        match action {
            DeckCheck(r_ident) => self.deck_check(r_ident).await,
            DeckDump(count) => self.deck_dump(count).await,
            TimeExtension(rnd, dur) => self.time_extension(ctx, rnd, dur).await,
            Cut(caller_id, len) => self.cut(ctx, caller_id, len).await,
            PairRound(caller_id) => self.pair_round(ctx, caller_id).await,
            RemoveMatch(r_ident) => self.remove_match(r_ident, ctx).await,
            RecordResult(p_ident, result) => self.record_result(ctx, p_ident, result).await,
            ConfirmResult(p_ident) => self.confirm_result(ctx, p_ident).await,
            ConfirmAll => self.confirm_all(ctx).await,
            AdminRecordResult(r_ident, result) => {
                self.admin_record_result(ctx, r_ident, result).await
            }
            AdminConfirmResult(r_ident, p_ident) => {
                self.admin_confirm_result(ctx, r_ident, p_ident).await
            }
            DropPlayer(p_ident) => self.drop_player(ctx, p_ident).await,
            PruneDecks(caller_id) => self.prune_decks(ctx, caller_id).await,
            PrunePlayers(caller_id) => self.prune_players(ctx, caller_id).await,
            End(caller_id) => self.action_end(ctx, caller_id).await,
            Cancel(caller_id) => self.action_cancel(ctx, caller_id).await,
            GiveBye(p_ident) => self.give_bye(ctx, p_ident).await,
            GetRawStandings(count) => self.get_raw_standings(count).await,
            ViewAllPlayers => self.view_all_players().await,
            CreateStandings(mut channel) => {
                self.create_standings(ctx, Arc::make_mut(&mut channel))
                    .await
            }
            CreateTournamentStatus(mut channel) => {
                self.create_tournament_status(ctx, Arc::make_mut(&mut channel))
                    .await
            }
            ViewDecklist(p_ident, deck_name) => self.view_decklist(p_ident, deck_name).await,
            ViewPlayerDecks(p_ident) => self.view_player_decks(p_ident).await,
            ViewPlayerProfile(p_ident) => self.view_player_profile(p_ident).await,
            ViewMatchStatus(r_ident) => self.view_match_status(r_ident).await,
            RegisterPlayer(user_id) => self.register_player(ctx, user_id).await,
            AdminRegisterPlayer(user_id) => self.admin_register_player(ctx, user_id).await,
            ReRegisterPlayer(user_id) => self.reregister_player(ctx, user_id).await,
            AdminReRegisterPlayer(user_id) => self.admin_reregister_player(ctx, user_id).await,
            RegisterGuest(name) => self.register_guest(ctx, name).await,
            CreateMatch(raw_plyrs) => self.create_match(ctx, raw_plyrs).await,
            Operation(op) => self.general_operation(ctx, op).await,
            ExportTournament => self.export_tournament().await,
        }
    }

    async fn export_tournament(
        &self,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut output = tempfile().unwrap();
        let _ = write!(output, "{}", serde_json::to_string(&self.tourn).unwrap());
        let mut digest = MessageContent::empty();
        digest.with_str("Here you go!!");
        digest.with_attachment(format!("{}.json", self.tourn.name), tokio::fs::File::from_std(output));
        Ok(digest)
    }

    async fn get_raw_standings(
        &self,
        count: usize,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let standings = self.tourn.get_standings();
        let mut output = tempfile().unwrap();
        for (i, (id, _)) in standings.scores.iter().enumerate().take(count) {
            let _ = writeln!(output, "{i}) {}", self.resolve_player_name(id).unwrap());
        }
        let mut digest = MessageContent::empty();
        digest.with_str("Here you go!!");
        digest.with_attachment("standings.txt".into(), tokio::fs::File::from_std(output));
        Ok(digest)
    }

    async fn view_decklist(
        &self,
        p_ident: PlayerIdentifier,
        deck_name: String,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let plyr_id = match self.tourn.get_player_id(&p_ident) {
            Ok(id) => id,
            Err(err) => {
                digest.with_str(error_to_content(err));
                return Ok(digest);
            }
        };
        let deck = match self.tourn.get_player_deck(&p_ident, &deck_name) {
            Ok(deck) => deck,
            Err(err) => {
                digest.with_str(error_to_content(err));
                return Ok(digest);
            }
        };
        let title = format!("{}'s deck", self.get_player_mention(&plyr_id).unwrap());
        let sorted_deck = TypeSortedDeck::from(deck.clone());
        let fields = sorted_deck.embed_fields();
        digest.with_str("Here you go!");
        digest.with_embeds(safe_embeds(title, fields));
        Ok(digest)
    }

    async fn view_player_decks(
        &self,
        p_ident: PlayerIdentifier,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let plyr = match self.tourn.get_player(&p_ident) {
            Ok(plyr) => plyr,
            Err(err) => {
                digest.with_str(error_to_content(err));
                return Ok(digest);
            }
        };
        if plyr.decks.is_empty() {
            digest.with_str("That player has no decks.");
            return Ok(digest);
        }
        let mut embeds = Vec::with_capacity(plyr.decks.len());
        for (name, deck) in &plyr.decks {
            let sorted_deck = TypeSortedDeck::from(deck.clone());
            let fields = sorted_deck.embed_fields();
            embeds.extend(safe_embeds(name.clone(), fields));
        }
        digest.with_str("Here you go!!");
        digest.with_embeds(embeds);
        Ok(digest)
    }

    async fn view_player_profile(
        &mut self,
        p_ident: PlayerIdentifier,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let plyr_id = match self.tourn.get_player_id(&p_ident) {
            Ok(id) => id,
            Err(err) => {
                digest.with_str(error_to_content(err));
                return Ok(digest);
            }
        };
        let mention = self.get_player_mention(&plyr_id).unwrap();
        let fields = player_embed_info(plyr_id, self);
        digest.with_str("Here you go!!");
        digest.with_embeds(safe_embeds(format!("{mention}'s Profile"), fields));
        Ok(digest)
    }

    async fn view_all_players(&mut self) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        digest.with_str("Here are all the players!!");
        let players: GroupMap<String, PlayerStatus> = self
            .tourn
            .player_reg
            .players
            .iter()
            .map(|(id, plyr)| (self.resolve_player_name(id).unwrap(), plyr.status))
            .collect();
        let mut embed = CreateEmbed(HashMap::new());
        embed.fields(players.iter_right().map(|s| {
            let mut iter = players.get_left_iter(s).unwrap();
            (format!("{s}: {}", iter.len()), iter.join("\n"), true)
        }));
        digest.with_embeds(vec![embed]);
        Ok(digest)
    }

    async fn create_standings(
        &mut self,
        ctx: &Context,
        channel: &mut GuildChannel,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let resp = channel
            .send_message(&ctx.http, |m| m.content("\u{200b}"))
            .await?;
        self.standings_message = Some(resp);
        self.update_standings(ctx).await;
        let mut digest = MessageContent::empty();
        digest.with_str("Standings message created!!");
        Ok(digest)
    }

    async fn create_tournament_status(
        &mut self,
        ctx: &Context,
        channel: &mut GuildChannel,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let resp = channel
            .send_message(&ctx.http, |m| m.content("\u{200b}"))
            .await?;
        self.tourn_status = Some(resp);
        self.update_status(ctx).await;
        digest.with_str("Tournament status message created!!");
        Ok(digest)
    }

    async fn view_match_status(
        &mut self,
        r_ident: RoundIdentifier,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let r_id = match self.tourn.get_round_id(&r_ident) {
            Ok(id) => id,
            Err(err) => {
                digest.with_str(error_to_content(err));
                return Ok(digest);
            }
        };
        let gr = self.get_guild_round(&r_id).unwrap();
        let (title, fields) = gr.embed_info();
        digest.with_str("Here you go!");
        digest.with_embeds(safe_embeds(title, fields));
        Ok(digest)
    }

    async fn deck_check(
        &self,
        r_ident: RoundIdentifier,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        match self.tourn.get_round(&r_ident) {
            Ok(rnd) => {
                let mut embeds = Vec::with_capacity(rnd.players.len());
                for plyr in rnd.players.iter().filter(|p| !rnd.drops.contains(p)) {
                    let player = self.tourn.get_player(&(*plyr).into()).unwrap();
                    for deck in player.decks.values() {
                        let title = format!("{}'s deck:", self.get_player_mention(&plyr).unwrap());
                        let sorted_deck = TypeSortedDeck::from(deck.clone());
                        let fields = sorted_deck.embed_fields();
                        embeds.extend_from_slice(&safe_embeds(title, fields));
                    }
                }
                digest.with_str("Here you go!!");
                digest.with_embeds(embeds);
            }
            Err(err) => {
                digest.with_str(error_to_content(err));
            }
        }
        Ok(digest)
    }

    async fn deck_dump(
        &mut self,
        count: usize,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        digest.with_str("Here you go!!");
        let standings = self.tourn.get_standings();
        let mut embeds = Vec::with_capacity(count);
        for plyr in standings.scores.iter().take(count).map(|(p, _)| p) {
            let player = self.tourn.get_player(&(*plyr).into()).unwrap();
            for deck in player.decks.values() {
                let title = format!("{}'s deck:", self.get_player_mention(&plyr).unwrap());
                let sorted_deck = TypeSortedDeck::from(deck.clone());
                let fields = sorted_deck.embed_fields();
                embeds.extend_from_slice(&safe_embeds(title, fields));
            }
        }
        digest.with_embeds(embeds);
        Ok(digest)
    }

    async fn remove_match(
        &mut self,
        r_ident: RoundIdentifier,
        ctx: &Context,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let r_id = match self.tourn.get_round_id(&r_ident) {
            Ok(id) => id,
            Err(err) => {
                digest.with_str(error_to_content(err));
                return Ok(digest);
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
            .apply_op(Utc::now(), TournOp::AdminOp(*SQUIRE_ACCOUNT_ID, RemoveRound(r_id)))
        {
            Ok(_) => "Match successfully removed.",
            Err(err) => error_to_content(err),
        };
        digest.with_str(content);
        self.update_status(ctx).await;
        self.update_standings(ctx).await;
        Ok(digest)
    }

    async fn prune_players(
        &mut self,
        ctx: &Context,
        caller_id: UserId,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let confirm = PrunePlayersConfirmation {
            tourn_id: self.tourn.id,
        };
        ctx.data
            .read()
            .await
            .get::<ConfirmationsContainer>()
            .unwrap()
            .insert(caller_id, Box::new(confirm));
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
        digest.with_text(format!("{content} Are you sure you want to? (!yes or !no)"));
        Ok(digest)
    }

    async fn prune_decks(
        &mut self,
        ctx: &Context,
        caller_id: UserId,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let confirm = PruneDecksConfirmation {
            tourn_id: self.tourn.id,
        };
        ctx.data
            .read()
            .await
            .get::<ConfirmationsContainer>()
            .unwrap()
            .insert(caller_id, Box::new(confirm));
        let content = if self.tourn.require_deck_reg {
            let max = self.tourn.max_deck_count;
            format!("Prune players' decks. After this, every player will have at most {max} decks. Are you sure you want to? (!yes or !no)")
        } else {
            "That tournament doesn't require deck registration. Pruning will do nothing."
                .to_string()
        };
        digest.with_text(content);
        Ok(digest)
    }

    async fn action_end(
        &mut self,
        ctx: &Context,
        caller_id: UserId,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let confirm = EndTournamentConfirmation {
            tourn_id: self.tourn.id,
        };
        ctx.data
            .read()
            .await
            .get::<ConfirmationsContainer>()
            .unwrap()
            .insert(caller_id, Box::new(confirm));
        digest.with_str(
            "You are about to end the tournament. Are you sure you want to? (!yes or !no)",
        );
        Ok(digest)
    }

    async fn action_cancel(
        &mut self,
        ctx: &Context,
        caller_id: UserId,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let confirm = CancelTournamentConfirmation {
            tourn_id: self.tourn.id,
        };
        ctx.data
            .read()
            .await
            .get::<ConfirmationsContainer>()
            .unwrap()
            .insert(caller_id, Box::new(confirm));
        digest.with_str(
            "You are about to cancel the tournament. Are you sure you want to? (!yes or !no)",
        );
        Ok(digest)
    }

    async fn cut(
        &mut self,
        ctx: &Context,
        caller_id: UserId,
        len: usize,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let confirm = CutToTopConfirmation {
            tourn_id: self.tourn.id,
            len,
        };
        ctx.data
            .read()
            .await
            .get::<ConfirmationsContainer>()
            .unwrap()
            .insert(caller_id, Box::new(confirm));
        digest.with_text(format!("You are about to cut the tournament to the top {len} players. Are you sure you want to? (!yes or !no)"));
        Ok(digest)
    }

    async fn record_result(
        &mut self,
        ctx: &Context,
        p_ident: PlayerIdentifier,
        result: RoundResult,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let p_id = match self.tourn.get_player_id(&p_ident) {
            Ok(id) => id,
            Err(err) => {
                digest.with_str(error_to_content(err));
                return Ok(digest);
            }
        };
        let op = TournOp::PlayerOp(p_id, RecordResult(result.clone()));
        match self.tourn.apply_op(Utc::now(), op) {
            Err(err) => {
                digest.with_str(error_to_content(err));
            }
            Ok(_) => {
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
                digest.with_str("Result recorded!! The current status of our round is:");
                if let Some(gr) = self.get_guild_round(&r_id) {
                    let (title, fields) = gr.embed_info();
                    digest.with_embeds(safe_embeds(title, fields));
                }
            }
        }
        Ok(digest)
    }
    
    async fn confirm_result(
        &mut self,
        ctx: &Context,
        p_ident: PlayerIdentifier,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let p_id = match self.tourn.get_player_id(&p_ident) {
            Ok(id) => id,
            Err(err) => {
                digest.with_str(error_to_content(err));
                return Ok(digest);
            }
        };
        let op = TournOp::PlayerOp(p_id, ConfirmResult);
        match self.tourn.apply_op(Utc::now(), op) {
            Err(err) => {
                digest.with_str(error_to_content(err));
            }
            Ok(OpData::ConfirmResult(_, status)) => {
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
                digest.with_str("Confirmation recorded!! The current status of our round is:");
                if let Some(tr) = self.get_tracking_round(&r_id) {
                    let (title, fields) = tr.embed_info();
                    digest.with_embeds(safe_embeds(title, fields));
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
        Ok(digest)
    }

    async fn confirm_all(
        &mut self,
        ctx: &Context,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let op = TournOp::AdminOp(*SQUIRE_ACCOUNT_ID, ConfirmAllRounds);
        let rnd_ids: Vec<_> = self.tourn.round_reg.rounds.values().filter_map(|r| r.is_active().then(|| r.id)).collect();
        match self.tourn.apply_op(Utc::now(), op) {
            Err(err) => {
                digest.with_str(error_to_content(err));
            }
            Ok(OpData::Nothing) => {
                let data = ctx
                    .data
                    .read()
                    .await;
                let update_sender = data
                    .get::<MatchUpdateSenderContainer>()
                    .unwrap();
                for id in rnd_ids {
                    self.clear_round_data(&id, &ctx.http).await;
                    let update = MatchUpdateMessage {
                        id,
                        update: MatchUpdate::ForceConfirmed,
                    };
                    let _ = update_sender.send(update);
                }
                digest.with_str("Confirmation recorded!! The current status of our round is:");
                self.update_status(ctx).await;
                self.update_standings(ctx).await;
            }
            _ => {
                unreachable!(
                    "Recording the result of a round returns and `Err` or `Ok(OpData::ConfirmResult)`)"
                );
            }
        }
        Ok(digest)
    }

    async fn admin_record_result(
        &mut self,
        ctx: &Context,
        r_ident: RoundIdentifier,
        result: RoundResult,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let r_id = match self.tourn.get_round_id(&r_ident) {
            Ok(id) => id,
            Err(err) => {
                digest.with_str(error_to_content(err));
                return Ok(digest);
            }
        };
        let op = TournOp::JudgeOp(
            (*SQUIRE_ACCOUNT_ID).into(),
            AdminRecordResult(r_id, result.clone()),
        );
        match self.tourn.apply_op(Utc::now(), op) {
            Err(err) => {
                digest.with_str(error_to_content(err));
            }
            Ok(_) => {
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
                digest.with_str("Result recorded!! The current status of the round is:");
                if let Some(tr) = self.get_tracking_round(&r_id) {
                    let (title, fields) = tr.embed_info();
                    digest.with_embeds(safe_embeds(title, fields));
                }
            }
        }
        Ok(digest)
    }

    async fn admin_confirm_result(
        &mut self,
        ctx: &Context,
        r_ident: RoundIdentifier,
        p_ident: PlayerIdentifier,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let r_id = match self.tourn.get_round_id(&r_ident) {
            Ok(id) => id,
            Err(err) => {
                digest.with_str(error_to_content(err));
                return Ok(digest);
            }
        };
        let p_id = match self.tourn.get_player_id(&p_ident) {
            Ok(id) => id,
            Err(err) => {
                digest.with_str(error_to_content(err));
                return Ok(digest);
            }
        };
        let op = TournOp::JudgeOp((*SQUIRE_ACCOUNT_ID).into(), AdminConfirmResult(r_id, p_id));
        match self.tourn.apply_op(Utc::now(), op) {
            Err(err) => {
                digest.with_str(error_to_content(err));
            }
            Ok(OpData::ConfirmResult(_, status)) => {
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
                digest.with_str("Result recorded!! The current status of the round is:");
                if let Some(tr) = self.get_tracking_round(&r_id) {
                    let (title, fields) = tr.embed_info();
                    digest.with_embeds(safe_embeds(title, fields));
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
        Ok(digest)
    }

    async fn give_bye(
        &mut self,
        ctx: &Context,
        p_ident: PlayerIdentifier,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let p_id = match self.tourn.get_player_id(&p_ident) {
            Ok(id) => id,
            Err(err) => {
                digest.with_str(error_to_content(err));
                return Ok(digest);
            }
        };
        let op = TournOp::AdminOp(*SQUIRE_ACCOUNT_ID, GiveBye(p_id));
        match self.tourn.apply_op(Utc::now(), op) {
            Err(err) => {
                digest.with_str(error_to_content(err));
            }
            Ok(_) => {
                self.update_status(ctx).await;
                self.update_standings(ctx).await;
                digest.with_str("Bye successfully given!!");
                let mention = self
                    .players
                    .get_left(&p_id)
                    .map(|id| id.mention().to_string())
                    .unwrap_or_else(|| self.guests.get_left(&p_id).unwrap().clone());
                self.pairings_channel
                    .send_message(&ctx.http, |m| {
                        m.content(format!("{mention}, you have been given a bye!"))
                    })
                    .await?;
            }
        }
        Ok(digest)
    }

    async fn register_player(
        &mut self,
        ctx: &Context,
        user_id: UserId,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let content = match self.tourn.apply_op(Utc::now(), TournOp::JudgeOp(
            (*SQUIRE_ACCOUNT_ID).into(),
            RegisterGuest(user_id.to_string()),
        )) {
            Ok(data) => {
                if let OpData::RegisterPlayer(id) = data {
                    self.players.insert(user_id, id);
                }
                self.update_status(ctx).await;
                "You have been successfully registered!!"
            }
            Err(err) => error_to_content(err),
        };
        digest.with_str(content);
        ctx.cache
            .guild(&self.guild_id)
            .unwrap()
            .member(ctx, user_id)
            .await
            .unwrap()
            .add_role(ctx, self.tourn_role.id)
            .await?;
        Ok(digest)
    }

    async fn reregister_player(
        &mut self,
        ctx: &Context,
        user_id: UserId,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let content = match self.tourn.apply_op(Utc::now(), TournOp::JudgeOp(
            (*SQUIRE_ACCOUNT_ID).into(),
            ReRegisterGuest(user_id.to_string()),
        )) {
            Ok(data) => {
                if let OpData::RegisterPlayer(id) = data {
                    self.players.insert(user_id, id);
                }
                self.update_status(ctx).await;
                "You have been successfully re-registered!!"
            }
            Err(err) => error_to_content(err),
        };
        digest.with_str(content);
        ctx.cache
            .guild(&self.guild_id)
            .unwrap()
            .member(ctx, user_id)
            .await
            .unwrap()
            .add_role(ctx, self.tourn_role.id)
            .await?;
        Ok(digest)
    }

    async fn admin_reregister_player(
        &mut self,
        ctx: &Context,
        user_id: UserId,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let content = match self.tourn.apply_op(Utc::now(), TournOp::JudgeOp(
            (*SQUIRE_ACCOUNT_ID).into(),
            ReRegisterGuest(user_id.to_string()),
        )) {
            Ok(data) => {
                if let OpData::RegisterPlayer(id) = data {
                    self.players.insert(user_id, id);
                }
                self.update_status(ctx).await;
                "Player successfully registered!!"
            }
            Err(err) => error_to_content(err),
        };
        digest.with_str(content);
        ctx.cache
            .guild(&self.guild_id)
            .unwrap()
            .member(ctx, user_id)
            .await
            .unwrap()
            .add_role(ctx, self.tourn_role.id)
            .await?;
        Ok(digest)
    }

    async fn admin_register_player(
        &mut self,
        ctx: &Context,
        user_id: UserId,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let content = match self.tourn.apply_op(Utc::now(), TournOp::JudgeOp(
            (*SQUIRE_ACCOUNT_ID).into(),
            RegisterGuest(user_id.to_string()),
        )) {
            Ok(data) => {
                if let OpData::RegisterPlayer(id) = data {
                    self.players.insert(user_id, id);
                }
                self.update_status(ctx).await;
                "Player successfully registered!!"
            }
            Err(err) => error_to_content(err),
        };
        digest.with_str(content);
        ctx.cache
            .guild(&self.guild_id)
            .unwrap()
            .member(ctx, user_id)
            .await
            .unwrap()
            .add_role(ctx, self.tourn_role.id)
            .await?;
        Ok(digest)
    }

    async fn register_guest(
        &mut self,
        ctx: &Context,
        name: String,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let content = match self.tourn.apply_op(Utc::now(), TournOp::JudgeOp(
            (*SQUIRE_ACCOUNT_ID).into(),
            RegisterGuest(name.clone()),
        )) {
            Ok(data) => {
                if let OpData::RegisterPlayer(id) = data {
                    self.guests.insert(name, id);
                }
                self.update_status(ctx).await;
                "Guest successfully registered!!"
            }
            Err(err) => error_to_content(err),
        };
        digest.with_str(content);
        Ok(digest)
    }

    async fn drop_player(
        &mut self,
        ctx: &Context,
        p_ident: PlayerIdentifier,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let p_id = match self.tourn.get_player_id(&p_ident) {
            Ok(id) => id,
            Err(err) => {
                digest.with_str(error_to_content(err));
                return Ok(digest);
            }
        };
        let op = TournOp::AdminOp(*SQUIRE_ACCOUNT_ID, AdminDropPlayer(p_id));
        match self.tourn.apply_op(Utc::now(), op) {
            Err(err) => {
                digest.with_str(error_to_content(err));
            }
            Ok(_) => {
                let data = ctx.data.read().await;
                let sender = data.get::<MatchUpdateSenderContainer>().unwrap();
                for rnd in self.tourn.get_player_rounds(&p_ident).unwrap() {
                    let _ = sender.send(MatchUpdateMessage {
                        id: rnd.id,
                        update: MatchUpdate::DropPlayer(p_id),
                    });
                }
                digest.with_str("Player successfully dropped.");
                self.update_status(ctx).await;
                self.update_standings(ctx).await;
                if let Some(u_id) = self.get_user_id(&p_id) {
                    ctx.cache
                        .guild(&self.guild_id)
                        .unwrap()
                        .member(ctx, u_id)
                        .await
                        .unwrap()
                        .remove_role(ctx, self.tourn_role.id)
                        .await?;
                }
            }
        }
        Ok(digest)
    }

    async fn create_match(
        &mut self,
        ctx: &Context,
        mut raw_plyrs: Vec<String>,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        // If the last "player" has the same name as the tournament, we ignore it.
        if raw_plyrs
            .last()
            .map(|name| &self.tourn.name == name)
            .unwrap_or_default()
        {
            raw_plyrs.pop();
        }
        let mut plyr_ids = Vec::with_capacity(raw_plyrs.len());
        let guild = ctx.cache.guild(self.guild_id).unwrap();
        for name in raw_plyrs {
            match user_id_resolver(&name, &guild)
                .await
                .and_then(|id| self.players.get_right(&id))
                .or_else(|| self.guests.get_right(&name))
            {
                Some(id) => {
                    plyr_ids.push((*id).into());
                }
                None => {
                    digest.with_text(format!("'{name}' is not registered for that tournament."));
                    return Ok(digest);
                }
            }
        }
        match self
            .tourn
            .apply_op(Utc::now(), TournOp::AdminOp(*SQUIRE_ACCOUNT_ID, CreateRound(plyr_ids)))
        {
            Ok(OpData::CreateRound(r_id)) => {
                let rnd = self.tourn.get_round(&(r_id.into())).unwrap().clone();
                self.create_round_data(
                    &ctx,
                    &ctx.cache.guild(self.guild_id).unwrap(),
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
                digest.with_str("Match successfully created!!");
                if let Some(gr) = self.get_guild_round(&rnd.id) {
                    let (title, fields) = gr.embed_info();
                    digest.with_embeds(safe_embeds(title, fields));
                }
            }
            Err(err) => {
                digest.with_str(error_to_content(err));
            }
            _ => {
                unreachable!("Creating a round returns and `Err` or `Ok(OpData::CreateRound)`)");
            }
        }
        Ok(digest)
    }

    async fn pair_round(
        &mut self,
        ctx: &Context,
        caller_id: UserId,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let confirm = PairRoundConfirmation {
            tourn_id: self.tourn.id,
        };
        ctx.data
            .read()
            .await
            .get::<ConfirmationsContainer>()
            .unwrap()
            .insert(caller_id, Box::new(confirm));
        digest.with_str("You are about to pair the next round of the tournament. Are you sure you want to? (!yes or !no)");
        self.update_status(ctx).await;
        Ok(digest)
    }

    async fn time_extension(
        &mut self,
        ctx: &Context,
        r_ident: RoundIdentifier,
        dur: Duration,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        let r_id = match self.tourn.get_round_id(&r_ident) {
            Ok(id) => id,
            Err(err) => {
                digest.with_str(error_to_content(err));
                return Ok(digest);
            }
        };
        let content = match self.tourn.apply_op(Utc::now(), TournOp::JudgeOp(
            (*SQUIRE_ACCOUNT_ID).into(),
            TimeExtension(r_id, dur),
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
                        id: r_id,
                        update: MatchUpdate::TimeExtention(dur),
                    });
                "Match successfully removed."
            }
        };
        digest.with_str(content);
        Ok(digest)
    }

    async fn general_operation(
        &mut self,
        ctx: &Context,
        op: TournOp,
    ) -> Result<MessageContent, Box<dyn Error + Send + Sync>> {
        let mut digest = MessageContent::empty();
        digest.with_str(op_to_content(&op));
        if let Err(err) = self.tourn.apply_op(Utc::now(), op) {
            digest.with_str(error_to_content(err));
        } else {
            self.update_status(ctx).await;
        };
        Ok(digest)
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
