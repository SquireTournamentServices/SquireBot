use std::collections::HashMap;

use cycle_map::CycleMap;
use serenity::{
    builder::CreateEmbed,
    model::{channel::Message, id::UserId},
    CacheAndHttp,
};

use squire_core::{
    player_registry::PlayerIdentifier, scoring::Standings, standard_scoring::StandardScore,
    swiss_pairings::PlayerId, tournament::Tournament,
};

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
        let mut name = if let Some(u_id) = plyrs.get_left(&id) {
            format!("{i}) <@{u_id}>\n")
        } else {
            format!(
                "{i}), {}\n",
                tourn.get_player(&PlayerIdentifier::Id(id)).unwrap().name
            )
        };
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
