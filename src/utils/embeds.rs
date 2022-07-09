use std::{
    collections::HashMap,
    fmt::{Display, Write},
};

use itertools::Itertools;
use serenity::{
    builder::CreateEmbed,
    client::Cache,
    http::CacheHttp,
    model::{
        channel::Message,
        id::{ChannelId, UserId},
    },
    utils::Colour,
    CacheAndHttp,
};

use cycle_map::CycleMap;
use squire_lib::{
    player_registry::PlayerIdentifier,
    round::Round,
    scoring::Standings,
    standard_scoring::StandardScore,
    swiss_pairings::PlayerId,
    tournament::{PairingSystem, ScoringSystem, Tournament, TournamentStatus},
};

use crate::utils::tourn_resolver::player_name_resolver;

use crate::model::guild_tournament::{self, GuildTournament};

pub fn embed_fields<I, T>(iter: I) -> Vec<String>
where
    I: Iterator<Item = T>,
    T: Display,
{
    let mut digest = Vec::new();
    let mut buffer = String::with_capacity(1024);
    for t in iter {
        let s = t.to_string();
        if buffer.len() + s.len() > 1024 {
            digest.push(buffer.clone());
            buffer.clear()
        }
        buffer += &s;
    }
    digest.push(buffer);
    digest
}

pub async fn update_standings_message(
    cache: &CacheAndHttp,
    mut msg: &mut Message,
    plyrs: &CycleMap<UserId, PlayerId>,
    tourn: &Tournament,
    mut standings: Standings<StandardScore>,
) {
    let mut embeds: Vec<CreateEmbed> = Vec::with_capacity(10);
    let mut e = CreateEmbed(HashMap::new());
    let mut name_buffer = String::with_capacity(1024);
    let mut score_buffer = String::with_capacity(1024);
    for (i, (id, score)) in standings.scores.drain(0..).enumerate() {
        let mut name = format!("{i}) {}", player_name_resolver(id, plyrs, tourn));
        let mut score_s = String::new();
        score_s += &if score.include_match_points {
            format!("{:.2}, ", score.match_points)
        } else if score.include_game_points {
            format!("{:.2}, ", score.game_points)
        } else {
            "".to_string()
        };
        score_s += &if score.include_mwp {
            format!("{:.2}, ", score.mwp)
        } else if score.include_gwp {
            format!("{:.2}, ", score.gwp)
        } else {
            "".to_string()
        };
        score_s += &if score.include_opp_mwp {
            format!("{:.2}", score.opp_mwp)
        } else if score.include_opp_gwp {
            format!("{:.2}", score.opp_gwp)
        } else {
            "".to_string()
        };
        score_s += "\n";
        if name.len() + name_buffer.len() > 1024 || score_s.len() + score_buffer.len() > 1024 {
            e.field("Name:", name_buffer.clone(), true);
            e.field("Points | Percent | Opp. %", score_buffer.clone(), true);
            embeds.push(e);
            e = CreateEmbed(HashMap::new());
            if embeds.len() == 10 {
                break;
            }
            name_buffer.clear();
            score_buffer.clear();
        }
        name_buffer += &name;
        score_buffer += &score_s;
    }
    if embeds.len() < 10 {
        e.field("Name:", name_buffer.clone(), true);
        e.field("Points | Percent | Opp. %", score_buffer.clone(), true);
        embeds.push(e);
    }
    let _ = msg.edit(cache, |m| m.set_embeds(embeds)).await;
}

pub async fn update_match_message(
    cache: &CacheAndHttp,
    mut msg: &mut Message,
    has_table_number: bool,
    vc_id: Option<ChannelId>,
    tc_id: Option<ChannelId>,
    plyrs: &CycleMap<UserId, PlayerId>,
    tourn: &Tournament,
    round: &Round,
) {
    let _ = msg
        .edit(cache, |m| {
            m.embed(|e| {
                let mut e = e.title(if has_table_number {
                    format!(
                        "Match #{}: Table {}",
                        round.match_number, round.table_number
                    )
                } else {
                    format!("Match #{}:", round.match_number)
                });
                if !round.is_certified() {
                    e.field(
                        "Time left:",
                        format!("{} min", round.time_left().as_secs() / 60),
                        false,
                    );
                } else {
                    e.field(
                        "Winner:",
                        player_name_resolver(round.winner.clone().unwrap(), plyrs, tourn),
                        false,
                    );
                }
                e.field("Status:", round.status.to_string(), false);
                if let Some(vc) = vc_id {
                    e.field("Voice Channel:", format!("<#{vc}"), false);
                }
                if let Some(tc) = tc_id {
                    e.field("Text Channel:", format!("<#{tc}"), false);
                }
                e.field(
                    "Players:",
                    round
                        .players
                        .iter()
                        .map(|id| player_name_resolver(id.clone(), plyrs, tourn))
                        .join("\n"),
                    false,
                )
            })
        })
        .await;
}

// Tournament contains the message
pub async fn update_status_message(cache: &impl CacheHttp, tourn: &mut GuildTournament) {
    let mut discord_info = format!("tournament role: <@&{}>\n", tourn.tourn_role.id);
    let _ = writeln!(discord_info, "Judge role: <@&{}>", tourn.judge_role);
    let _ = writeln!(
        discord_info,
        "Tournament admin role: <@&{}>",
        tourn.tourn_admin_role
    );
    let _ = writeln!(
        discord_info,
        "Pairings channel: <#{}>",
        tourn.pairings_channel.id
    );
    let _ = writeln!(
        discord_info,
        "Matches category: <#{}>",
        tourn.matches_category.id
    );
    let mut settings_info = format!("format: {}", tourn.tourn.format);
    let _ = writeln!(
        settings_info,
        "Pairing method: {}",
        match tourn.tourn.pairing_sys {
            PairingSystem::Swiss(_) => "Swiss",
            PairingSystem::Fluid(_) => "Fluid",
        }
    );
    let _ = writeln!(
        settings_info,
        "Scoring method: {}",
        match tourn.tourn.scoring_sys {
            ScoringSystem::Standard(_) => "Standard",
        }
    );
    let _ = writeln!(
        settings_info,
        "Registration: {}",
        if tourn.tourn.reg_open {
            "Open"
        } else {
            "Closed"
        }
    );
    let _ = writeln!(settings_info, "Match size: {}", tourn.tourn.game_size);
    let _ = writeln!(
        settings_info,
        "Assign table number:{}\n",
        if tourn.tourn.use_table_number {
            "True"
        } else {
            "False"
        }
    );
    let _ = writeln!(
        settings_info,
        "Require checkin: {}",
        if tourn.tourn.require_check_in {
            "True"
        } else {
            "False"
        }
    );
    let _ = writeln!(
        settings_info,
        "Require deck reg: {}",
        if tourn.tourn.require_deck_reg {
            "True"
        } else {
            "False"
        }
    );
    if tourn.tourn.require_deck_reg {
        let _ = writeln!(
            settings_info,
            "Min deck count: {}",
            tourn.tourn.min_deck_count
        );
        let _ = writeln!(
            settings_info,
            "Max deck count: {}",
            tourn.tourn.max_deck_count
        );
    }
    let mut player_info = format!(
        "{} players are registered.",
        tourn.tourn.player_reg.active_player_count()
    );
    if tourn.tourn.require_deck_reg {
        let player_count = tourn
            .tourn
            .player_reg
            .players
            .iter()
            .filter(|(_, p)| p.decks.len() > tourn.tourn.min_deck_count as usize)
            .count();
        let _ = write!(
            player_info,
            "{} of them have registered the minimum number of decks.",
            player_count
        );
    }
    if tourn.tourn.require_check_in {
        let _ = write!(
            player_info,
            "{} of them have checked in.",
            tourn.tourn.player_reg.count_check_ins()
        );
    }
    let mut match_info = format!(
        "New matches will be {} minutes long.",
        tourn.tourn.round_reg.length.as_secs() / 60
    );
    let match_count = tourn.tourn.round_reg.active_round_count();
    let _ = write!(
        match_info,
        "There are {} matches that are yet to be certified.",
        match_count
    );
    let color = match tourn.tourn.status {
        TournamentStatus::Planned => Colour::GOLD,
        TournamentStatus::Started => Colour::FOOYOO,
        TournamentStatus::Frozen => Colour::ROHRKATZE_BLUE,
        TournamentStatus::Ended | TournamentStatus::Cancelled => Colour::DARK_GREY,
    };
    let msg = tourn.tourn_status.as_mut().unwrap();
    let _ = msg
        .edit(cache, |m| {
            m.embed(|e| {
                e.color(color)
                    .title(format!("{} Status:", tourn.tourn.name))
                    .field("Discord Info:", discord_info, false)
                    .field("Tournament Settings Info:", settings_info, false)
                    .field("Player Info:", player_info, false)
                    .field("Match Info:", match_info, false)
            })
        })
        .await;
}
