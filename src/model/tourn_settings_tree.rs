use std::fmt::Write;

use serde::{Deserialize, Serialize};
use serenity::builder::CreateEmbed;

use squire_lib::{settings::TournamentSettingsTree, tournament::TournamentPreset::Swiss};

pub fn populate_embed<'a>(
    tree: &TournamentSettingsTree,
    embed: &'a mut CreateEmbed,
) -> &'a mut CreateEmbed {
    let data = format!("Format: {}\nFirst Table Number: {}\nTable Numbers?: {}\nMin. Deck Count: {}\nMax. Deck Count: {}\nRequire Checkin?: {}\nRequire Decks?: {}\n",
    tree.format,
    tree.starting_table_number,
    tree.use_table_numbers,
    tree.min_deck_count,
    tree.max_deck_count,
    tree.require_check_in,
    tree.require_deck_reg,);
    embed.field("Base Tournament Settings:", data, true);

    let data = format!("Match Size: {}\nRepair Tolerance: {}\nPairing Algorithm: {}\n\n**Swiss Settings**:\nDo Checkins?: {}\n\n**Fluid Settings**:",
    tree.pairing_settings.match_size,
    tree.pairing_settings.repair_tolerance,
    tree.pairing_settings.algorithm,
    tree.pairing_settings.swiss.do_check_ins);
    embed.field("Pairing Settings:", data, true);

    let data = format!(
        "**Standard Scoring**\n\
    Match Win: {}\n\
    Match Draw: {}\n\
    Match Loss: {}\n\
    Game Win: {}\n\
    Game Draw: {}\n\
    Game Loss: {}\n\
    Byes: {}\n\
    Include Byes: {}\n\
    Include MP: {}\n\
    Include GP: {}\n\
    Include MWP: {}\n\
    Include GWP: {}\n\
    Include OMWP: {}\n\
    Include OGWP: {}",
        tree.scoring_settings.standard.match_win_points,
        tree.scoring_settings.standard.match_draw_points,
        tree.scoring_settings.standard.match_loss_points,
        tree.scoring_settings.standard.game_win_points,
        tree.scoring_settings.standard.game_draw_points,
        tree.scoring_settings.standard.game_loss_points,
        tree.scoring_settings.standard.bye_points,
        tree.scoring_settings.standard.include_byes,
        tree.scoring_settings.standard.include_match_points,
        tree.scoring_settings.standard.include_game_points,
        tree.scoring_settings.standard.include_mwp,
        tree.scoring_settings.standard.include_gwp,
        tree.scoring_settings.standard.include_opp_mwp,
        tree.scoring_settings.standard.include_opp_gwp,
    );
    embed.field("Scoring Settings:", data, true);

    embed
}
