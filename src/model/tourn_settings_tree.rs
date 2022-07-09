use std::fmt::Write;

use serde::{Deserialize, Serialize};
use serenity::builder::CreateEmbed;

use squire_lib::settings::{
    FluidPairingsSetting, StandardScoringSetting, SwissPairingsSetting, TournamentSetting,
};

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct TournSettingsTree {
    pub(crate) format: TournamentSetting,
    pub(crate) min_deck_count: TournamentSetting,
    pub(crate) max_deck_count: TournamentSetting,
    pub(crate) require_check_in: TournamentSetting,
    pub(crate) require_deck_reg: TournamentSetting,
    pub(crate) pairing_settings: PairingSettingsTree,
    pub(crate) scoring_settings: ScoringSettingsTree,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct PairingSettingsTree {
    pub(crate) swiss: SwissPairingsSettingsTree,
    pub(crate) fluid: FluidPairingsSettingsTree,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct ScoringSettingsTree {
    pub(crate) standard: StandardScoringSettingsTree,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct SwissPairingsSettingsTree {
    pub(crate) match_size: SwissPairingsSetting,
    pub(crate) do_checkins: SwissPairingsSetting,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct FluidPairingsSettingsTree {
    pub(crate) match_size: FluidPairingsSetting,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub struct StandardScoringSettingsTree {
    pub(crate) match_win_points: StandardScoringSetting,
    pub(crate) match_draw_points: StandardScoringSetting,
    pub(crate) match_loss_points: StandardScoringSetting,
    pub(crate) game_win_points: StandardScoringSetting,
    pub(crate) game_draw_points: StandardScoringSetting,
    pub(crate) game_loss_points: StandardScoringSetting,
    pub(crate) bye_points: StandardScoringSetting,
    pub(crate) include_byes: StandardScoringSetting,
    pub(crate) include_match_points: StandardScoringSetting,
    pub(crate) include_game_points: StandardScoringSetting,
    pub(crate) include_mwp: StandardScoringSetting,
    pub(crate) include_gwp: StandardScoringSetting,
    pub(crate) include_opp_mwp: StandardScoringSetting,
    pub(crate) include_opp_gwp: StandardScoringSetting,
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

    pub fn populate_embed<'a>(&self, embed: &'a mut CreateEmbed) -> &'a mut CreateEmbed {
        let mut data = String::new();
        let _ = writeln!(data, "{}", self.format);
        let _ = writeln!(data, "{}", self.min_deck_count);
        let _ = writeln!(data, "{}", self.max_deck_count);
        let _ = writeln!(data, "{}", self.require_check_in);
        let _ = write!(data, "{}", self.require_deck_reg);
        self.scoring_settings
            .populate_embed(self.pairing_settings.populate_embed(embed.field(
                "Tournament Settings:",
                data,
                true,
            )))
    }
}
impl PairingSettingsTree {
    pub fn new() -> Self {
        Self {
            swiss: SwissPairingsSettingsTree::new(),
            fluid: FluidPairingsSettingsTree::new(),
        }
    }

    pub fn populate_embed<'a>(&self, embed: &'a mut CreateEmbed) -> &'a mut CreateEmbed {
        self.swiss.populate_embed(self.fluid.populate_embed(embed))
    }
}
impl ScoringSettingsTree {
    pub fn new() -> Self {
        Self {
            standard: StandardScoringSettingsTree::new(),
        }
    }

    pub fn populate_embed<'a>(&self, embed: &'a mut CreateEmbed) -> &'a mut CreateEmbed {
        self.standard.populate_embed(embed)
    }
}
impl SwissPairingsSettingsTree {
    pub fn new() -> Self {
        Self {
            match_size: SwissPairingsSetting::MatchSize(2),
            do_checkins: SwissPairingsSetting::DoCheckIns(false),
        }
    }

    pub fn populate_embed<'a>(&self, embed: &'a mut CreateEmbed) -> &'a mut CreateEmbed {
        let mut data = String::new();
        let _ = writeln!(data, "{}", self.match_size);
        let _ = write!(data, "{}", self.do_checkins);
        embed.field("Swiss Pairings:", data, true)
    }
}
impl FluidPairingsSettingsTree {
    pub fn new() -> Self {
        Self {
            match_size: FluidPairingsSetting::MatchSize(4),
        }
    }

    pub fn populate_embed<'a>(&self, embed: &'a mut CreateEmbed) -> &'a mut CreateEmbed {
        let data = format!("{}", self.match_size);
        embed.field("Fluid Pairings:", data, true)
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

    pub fn populate_embed<'a>(&self, embed: &'a mut CreateEmbed) -> &'a mut CreateEmbed {
        let mut data = String::new();
        let _ = writeln!(data, "{}", self.match_win_points);
        let _ = writeln!(data, "{}", self.match_draw_points);
        let _ = writeln!(data, "{}", self.match_loss_points);
        let _ = writeln!(data, "{}", self.game_win_points);
        let _ = writeln!(data, "{}", self.game_draw_points);
        let _ = writeln!(data, "{}", self.game_loss_points);
        let _ = writeln!(data, "{}", self.bye_points);
        let _ = writeln!(data, "{}", self.include_byes);
        let _ = writeln!(data, "{}", self.include_match_points);
        let _ = writeln!(data, "{}", self.include_game_points);
        let _ = writeln!(data, "{}", self.include_mwp);
        let _ = writeln!(data, "{}", self.include_gwp);
        let _ = writeln!(data, "{}", self.include_opp_mwp);
        let _ = writeln!(data, "{}", self.include_opp_gwp);
        embed.field("Standard Scoring:", data, true)
    }
}
