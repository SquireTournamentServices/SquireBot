use std::{
    collections::HashMap,
    fmt::{Display, Write},
};

use serenity::{builder::CreateEmbed, prelude::Mentionable};

use squire_lib::{
    identifiers::PlayerId,
    pairings::PairingStyle,
    scoring::{ScoringSystem, StandardScore, Standings},
};

use crate::model::guilds::GuildTournament;

const FIELD_CAPACITY: usize = 1024;
const EMBED_CAPACITY: usize = 2048;

pub type StringFields = Vec<(String, Vec<String>, &'static str, bool)>;

/// Takes the data from an embed and divides it between multiple embed to ensure the invariants
/// needed for an embed. Namely:
///  - Each field has at most 1024 characters (including title)
///  - Each embed has at most 2048 characters (including title)
///  - No field is empty
///  
/// NOTE: There will still be problems if single title or field item is greater than its
/// respective limit. Under normal situations, this should not be an issue
pub fn safe_embeds<'a, I, F, T>(title: String, fields: I) -> Vec<CreateEmbed>
where
    I: IntoIterator<Item = (String, F, &'a str, bool)>,
    F: IntoIterator<Item = T>,
    T: Display,
{
    let mut digest = Vec::new();
    let mut safe_fields: Vec<(String, String, bool)> = Vec::new();
    let mut field_buffer = String::with_capacity(FIELD_CAPACITY);
    for field in fields {
        let field_cap = FIELD_CAPACITY - field.0.len();
        let delim_len = field.2.len();
        let _ = write!(field_buffer, "\u{200b}");
        for item in field.1.into_iter().map(|i| i.to_string()) {
            if field_buffer.len() + item.len() + delim_len > field_cap {
                safe_fields.push((field.0.clone(), field_buffer.clone(), field.3));
                field_buffer.clear();
                let _ = write!(field_buffer, "\u{200b}");
            }
            let _ = write!(field_buffer, "{}{}", item, field.2);
        }
        safe_fields.push((field.0, field_buffer.clone(), field.3));
        field_buffer.clear();
    }
    // At this point, `safe_fields` contain fields that are at most 1024 (with title)
    let mut creator = CreateEmbed(HashMap::new());
    creator.title(title.clone());
    let embed_cap = EMBED_CAPACITY - title.len();
    let mut embed_len = 0;
    for field in safe_fields {
        if embed_len + field.0.len() + field.1.len() > embed_cap {
            digest.push(creator);
            creator = CreateEmbed(HashMap::new());
            creator.title(title.clone());
        }
        embed_len += field.0.len() + field.1.len();
        creator.field(field.0, field.1, field.2);
    }
    // Now, each embed has properly sized fields
    digest.push(creator);
    digest
}

pub fn player_embed_info(
    plyr_id: PlayerId,
    g_tourn: &GuildTournament,
) -> Vec<(String, Vec<String>, &'static str, bool)> {
    let plyr = g_tourn.tourn.get_player(&plyr_id.into()).unwrap();
    let mut digest = Vec::with_capacity(4);
    let bio = vec![
        format!("Name: {}", g_tourn.get_player_mention(&plyr_id).unwrap()),
        format!(
            "Discord ID: {}",
            g_tourn
                .get_user_id(&plyr_id)
                .map(|id| id.mention().to_string())
                .unwrap_or_else(|| "None".into())
        ),
        format!("Gamer Tag: {}", plyr.game_name.as_deref().unwrap_or("None")),
        format!("Tournament ID: {plyr_id}",),
    ];
    digest.push(("Bio Info:".into(), bio, "\n", true));
    let status = vec![format!("Status: {}", plyr.status)];
    digest.push(("Status Info:".into(), status, "\n", true));
    let decks = plyr.deck_ordering.clone();
    digest.push(("Deck Names:".into(), decks, "\n", true));
    let rnds = g_tourn
        .tourn
        .get_player_rounds(&plyr_id.into())
        .unwrap()
        .into_iter()
        .map(|rnd| format!("Round #{}: {}", rnd.match_number, rnd.status))
        .collect();
    digest.push(("Round Info:".into(), rnds, "\n", true));
    digest
}

pub fn tournament_embed_info(
    g_tourn: &GuildTournament,
) -> Vec<(String, Vec<String>, &'static str, bool)> {
    let mut digest = Vec::new();
    let discord_info = vec![
        format!("Tournament role: {}", g_tourn.tourn_role.mention()),
        format!("Judge role: {}", g_tourn.judge_role.mention()),
        format!(
            "Tournament admin role: {}",
            g_tourn.tourn_admin_role.mention()
        ),
        format!(
            "Pairings channel: {}",
            g_tourn.pairings_channel.id.mention()
        ),
        format!(
            "Matches category: {}",
            g_tourn.matches_category.id.mention()
        ),
    ];
    digest.push(("Discord Info:".into(), discord_info, "\n", true));
    let mut settings_info = vec![
        format!("Format: {}", g_tourn.tourn.format),
        format!(
            "Pairing method: {}",
            match g_tourn.tourn.pairing_sys.style {
                PairingStyle::Swiss(_) => "Swiss",
                PairingStyle::Fluid(_) => "Fluid",
            }
        ),
        format!(
            "Scoring method: {}",
            match g_tourn.tourn.scoring_sys {
                ScoringSystem::Standard(_) => "Standard",
            }
        ),
        format!(
            "Registration: {}",
            if g_tourn.tourn.reg_open {
                "Open"
            } else {
                "Closed"
            }
        ),
        format!("Match size: {}", g_tourn.tourn.pairing_sys.match_size),
        format!(
            "Assign table number: {}",
            if g_tourn.tourn.use_table_number {
                "True"
            } else {
                "False"
            }
        ),
        format!(
            "Require checkin: {}",
            if g_tourn.tourn.require_check_in {
                "True"
            } else {
                "False"
            }
        ),
        format!(
            "Require deck reg: {}",
            if g_tourn.tourn.require_deck_reg {
                "True"
            } else {
                "False"
            }
        ),
    ];
    if g_tourn.tourn.require_deck_reg {
        settings_info.push(format!("Min deck count: {}", g_tourn.tourn.min_deck_count));
        settings_info.push(format!("Max deck count: {}", g_tourn.tourn.max_deck_count));
    }
    digest.push(("Settings Info:".into(), settings_info, "\n", true));
    let mut player_info = vec![format!(
        "{} players are registered.",
        g_tourn.tourn.player_reg.active_player_count()
    )];
    if g_tourn.tourn.require_deck_reg {
        let min_count = g_tourn
            .tourn
            .player_reg
            .players
            .iter()
            .filter(|(_, p)| p.decks.len() > g_tourn.tourn.min_deck_count as usize)
            .count();
        player_info.push(format!(
            "{} of them have registered at least the minimum number of decks.",
            min_count
        ));
        let max_count = g_tourn
            .tourn
            .player_reg
            .players
            .iter()
            .filter(|(_, p)| p.decks.len() > g_tourn.tourn.max_deck_count as usize)
            .count();
        player_info.push(format!(
            "{} of them have registered more than the maximum number of decks.",
            max_count
        ));
    }
    if g_tourn.tourn.require_check_in {
        player_info.push(format!(
            "{} of them have checked in.",
            g_tourn.tourn.player_reg.count_check_ins()
        ));
    }
    digest.push(("Player Info:".into(), player_info, " ", true));
    let completed_count = g_tourn
        .tourn
        .round_reg
        .rounds
        .values()
        .filter(|rnd| rnd.is_certified())
        .count();
    let active_count = g_tourn.tourn.round_reg.active_round_count();
    let match_info = vec![
        format!(
            "New matches will be {} minutes long.",
            g_tourn.tourn.round_reg.length.as_secs() / 60
        ),
        format!("There are {} completed matches.", completed_count),
        format!(
            "There are {} matches that are yet to be certified.",
            active_count
        ),
    ];
    digest.push(("Match Info:".into(), match_info, " ", true));
    digest
}

pub fn standings_embeds(
    mut standings: Standings<StandardScore>,
    g_tourn: &GuildTournament,
) -> Vec<CreateEmbed> {
    let mut embeds = Vec::with_capacity(10);
    let mut e = CreateEmbed(HashMap::new());
    let mut name_buffer = String::with_capacity(FIELD_CAPACITY);
    let mut score_buffer = String::with_capacity(FIELD_CAPACITY);
    for (i, (id, score)) in standings.scores.drain(0..).rev().enumerate() {
        let name = format!("{}) {}", i + 1, g_tourn.get_player_mention(&id).unwrap());
        let mut score_s = if score.include_match_points {
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
        if name.len() + name_buffer.len() > FIELD_CAPACITY || score_s.len() + score_buffer.len() > FIELD_CAPACITY {
            e.field("Name:", name_buffer.clone(), true);
            e.field("Points | Win % | Opp. W. %", score_buffer.clone(), true);
            embeds.push(e);
            e = CreateEmbed(HashMap::new());
            if embeds.len() == 9 {
                break;
            }
            name_buffer.clear();
            score_buffer.clear();
        }
        name_buffer += &name;
        name_buffer += "\n";
        score_buffer += &score_s;
        score_buffer += "\n";
    }
    if embeds.len() < 9 {
        e.field("Name:", name_buffer.clone(), true);
        e.field("Points | Win % | Opp. W. %", score_buffer.clone(), true);
        embeds.push(e);
    }
    embeds
}
