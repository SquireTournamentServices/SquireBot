use std::{
    collections::HashMap,
    fmt::{Display, Write},
};

use serenity::builder::CreateEmbed;

const FIELD_CAPACITY: usize = 1024;
const EMBED_CAPACITY: usize = 2048;

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

/*
pub async fn update_standings_message(
    cache: &CacheAndHttp,
    msg: &mut Message,
    plyrs: &CycleMap<UserId, PlayerId>,
    tourn: &Tournament,
    mut standings: Standings<StandardScore>,
) {
    let mut embeds: Vec<CreateEmbed> = Vec::with_capacity(10);
    let mut e = CreateEmbed(HashMap::new());
    let mut name_buffer = String::with_capacity(1024);
    let mut score_buffer = String::with_capacity(1024);
    for (i, (id, score)) in standings.scores.drain(0..).rev().enumerate() {
        let name = format!("{}) {}", i + 1, player_name_resolver(id, plyrs, tourn));
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
    println!("Attaching {} embeds", embeds.len());
    let _ = msg
        .edit(cache, |m| m.content("\u{200b}").set_embeds(embeds))
        .await;
}

// Tournament contains the message
pub async fn update_status_message(cache: &impl CacheHttp, tourn: &mut GuildTournament) {
    let mut discord_info = format!("Tournament role: <@&{}>\n", tourn.tourn_role.id);
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
    let mut settings_info = format!("Format: {}\n", tourn.tourn.format);
    let _ = writeln!(
        settings_info,
        "Pairing method: {}",
        match tourn.tourn.pairing_sys.style {
            PairingStyle::Swiss(_) => "Swiss",
            PairingStyle::Fluid(_) => "Fluid",
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
    let _ = writeln!(
        settings_info,
        "Match size: {}",
        tourn.tourn.pairing_sys.match_size
    );
    let _ = writeln!(
        settings_info,
        "Assign table number: {}",
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
        " There are {} matches that are yet to be certified.",
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
*/
