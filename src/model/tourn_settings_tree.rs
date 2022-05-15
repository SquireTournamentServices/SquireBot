use squire_core::settings::{
    FluidPairingsSetting, StandardScoringSetting, SwissPairingsSetting, TournamentSetting,
};

use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct TournSettingsTree {
    format: TournamentSetting,
    min_deck_count: TournamentSetting,
    max_deck_count: TournamentSetting,
    require_check_in: TournamentSetting,
    require_deck_reg: TournamentSetting,
    pairing_settings: PairingSettingsTree,
    scoring_settings: ScoringSettingsTree,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct PairingSettingsTree {
    swiss: SwissPairingsSettingsTree,
    fluid: FluidPairingsSettingsTree,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct ScoringSettingsTree {
    standard: StandardScoringSettingsTree,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct SwissPairingsSettingsTree {
    match_size: SwissPairingsSetting,
    do_checkins: SwissPairingsSetting,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct FluidPairingsSettingsTree {
    match_size: FluidPairingsSetting,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct StandardScoringSettingsTree {
    match_win_points: StandardScoringSetting,
    match_draw_points: StandardScoringSetting,
    match_loss_points: StandardScoringSetting,
    game_win_points: StandardScoringSetting,
    game_draw_points: StandardScoringSetting,
    game_loss_points: StandardScoringSetting,
    bye_points: StandardScoringSetting,
    include_byes: StandardScoringSetting,
    include_match_points: StandardScoringSetting,
    include_game_points: StandardScoringSetting,
    include_mwp: StandardScoringSetting,
    include_gwp: StandardScoringSetting,
    include_opp_mwp: StandardScoringSetting,
    include_opp_gwp: StandardScoringSetting,
}

impl TournSettingsTree {
    pub fn new() -> Self {
        Self {
            format: TournamentSetting::Format("Pioneer".to_string()),
            min_deck_count: TournamentSetting::MinDeckCount(0),
            max_deck_count: TournamentSetting::MaxDeckCount(2),
            require_check_in: TournamentSetting::RequireCheckIn(false),
            require_deck_reg: TournamentSetting::RequireDeckReg(false),
            pairing_settings: PairingSettingsTree::new(),
            scoring_settings: ScoringSettingsTree::new(),
        }
    }
}
impl PairingSettingsTree {
    pub fn new() -> Self {
        Self {
            swiss: SwissPairingsSettingsTree::new(),
            fluid: FluidPairingsSettingsTree::new(),
        }
    }
}
impl ScoringSettingsTree {
    pub fn new() -> Self {
        Self {
            standard: StandardScoringSettingsTree::new(),
        }
    }
}
impl SwissPairingsSettingsTree {
    pub fn new() -> Self {
        Self {
            match_size: SwissPairingsSetting::MatchSize(2),
            do_checkins: SwissPairingsSetting::DoCheckIns(false),
        }
    }
}
impl FluidPairingsSettingsTree {
    pub fn new() -> Self {
        Self {
            match_size: FluidPairingsSetting::MatchSize(4)
        }
    }
}
impl StandardScoringSettingsTree {
    pub fn new() -> Self {
        Self {
            match_win_points: StandardScoringSetting::MatchWinPoints(3.0),
            match_draw_points: StandardScoringSetting::MatchDrawPoints(1.0),
            match_loss_points: StandardScoringSetting::MatchLossPoints(0.0),
            game_win_points: StandardScoringSetting::GameWinPoints(3.0),
            game_draw_points: StandardScoringSetting::GameDrawPoints(1.0),
            game_loss_points: StandardScoringSetting::GameLossPoints(0.0),
            bye_points: StandardScoringSetting::ByePoints(3.0),
            include_byes: StandardScoringSetting::IncludeByes(true),
            include_match_points: StandardScoringSetting::IncludeMatchPoints(true),
            include_game_points: StandardScoringSetting::IncludeGamePoints(true),
            include_mwp: StandardScoringSetting::IncludeMwp(true),
            include_gwp: StandardScoringSetting::IncludeGwp(true),
            include_opp_mwp: StandardScoringSetting::IncludeOppMwp(true),
            include_opp_gwp: StandardScoringSetting::IncludeOppGwp(true),
        }
    }
}
