use std::collections::HashMap;

use cycle_map::CycleMap;
use itertools::Itertools;
use serenity::{
    builder::CreateEmbed,
    model::{
        channel::Message,
        id::{ChannelId, UserId},
    },
    CacheAndHttp,
};

use squire_core::{
    player_registry::PlayerIdentifier, round::Round, scoring::Standings,
    standard_scoring::StandardScore, swiss_pairings::PlayerId, tournament::Tournament,
};

use crate::model::guild_tournament::GuildTournament;

fn resolve_name(id: PlayerId, plyrs: &CycleMap<UserId, PlayerId>, tourn: &Tournament) -> String {
    if let Some(u_id) = plyrs.get_left(&id) {
        format!("<@{u_id}>\n")
    } else {
        format!(
            "{}\n",
            tourn.get_player(&PlayerIdentifier::Id(id)).unwrap().name
        )
    }
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
        let mut name = format!("{i}) {}", resolve_name(id, plyrs, tourn));
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
                        format!(
                            "{}",
                            resolve_name(round.winner.clone().unwrap(), plyrs, tourn)
                        ),
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
                        .map(|id| resolve_name(id.clone(), plyrs, tourn))
                        .join("\n"),
                    false,
                )
            })
        })
        .await;
}

pub async fn update_status_message(
    cache: &CacheAndHttp,
    mut msg: &mut Message,
    tournament: &GuildTournament,
) {
    todo!()
}
