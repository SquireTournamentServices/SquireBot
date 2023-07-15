use serenity::builder::CreateEmbed;

use squire_lib::settings::{
    FluidPairingSettingsTree, GeneralSettingsTree, PairingSettingsTree, PairingStyleSettingsTree,
    ScoringSettingsTree, ScoringStyleSettingsTree, TournamentSettingsTree,
};

pub fn populate_embed<'a>(
    tree: &TournamentSettingsTree,
    embed: &'a mut CreateEmbed,
) -> &'a mut CreateEmbed {
    populate_general_embed(&tree.general, embed);
    populate_pairing_embed(&tree.pairing, embed);
    populate_scoring_embed(&tree.scoring, embed);

    embed
}

fn populate_general_embed<'a>(tree: &GeneralSettingsTree, embed: &'a mut CreateEmbed) {
    let data = format!(
        "Format: {}\n
        First Table Number: {}\n
        Table Numbers?: {}\n
        Min. Deck Count: {}\n
        Max. Deck Count: {}\n
        Require Checkin?: {}\n
        Require Decks?: {}\n",
        tree.format,
        tree.starting_table_number,
        tree.use_table_number,
        tree.min_deck_count,
        tree.max_deck_count,
        tree.require_check_in,
        tree.require_deck_reg,
    );
    embed.field("Base Tournament Settings:", data, true);
}

fn populate_pairing_embed<'a>(tree: &PairingSettingsTree, embed: &'a mut CreateEmbed) {
    let common_data = format!(
        "Match Size: {}\n
        Repair Tolerance: {}\n
        Pairing Algorithm: {}\n\n",
        tree.common.match_size, tree.common.repair_tolerance, tree.common.algorithm,
    );
    let style_data = match &tree.style {
        PairingStyleSettingsTree::Swiss(tree) => {
            format!(
                "**Swiss Settings**:\n
                Do Checkins?: {}",
                tree.do_checkins,
            )
        }
        PairingStyleSettingsTree::Fluid(FluidPairingSettingsTree {}) => {
            format!("**Fluid Settings**:")
        }
    };
    let data = format!("{}{}", common_data, style_data);
    embed.field("Pairing Settings:", data, true);
}

fn populate_scoring_embed(tree: &ScoringSettingsTree, embed: &mut CreateEmbed) {
    let style_data = match &tree.style {
        ScoringStyleSettingsTree::Standard(tree) => format!(
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
            tree.match_win_points,
            tree.match_draw_points,
            tree.match_loss_points,
            tree.game_win_points,
            tree.game_draw_points,
            tree.game_loss_points,
            tree.bye_points,
            tree.include_byes,
            tree.include_match_points,
            tree.include_game_points,
            tree.include_mwp,
            tree.include_gwp,
            tree.include_opp_mwp,
            tree.include_opp_gwp,
        ),
    };
    embed.field("Scoring Settings:", style_data, true);
}
