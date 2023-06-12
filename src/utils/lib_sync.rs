/// This module does nothing of direct substance. Rather, it softly ensures that, when not compiling in
/// release mode, the there are commands for each tournament operation, tournament setting, and any
/// other input enums from squire_lib.
use squire_lib::{
    operations::TournOp,
    settings::{
        FluidPairingsSetting, PairingSetting, ScoringSetting, StandardScoringSetting,
        SwissPairingsSetting, TournamentSetting,
    },
};

fn check_tourn_ops(op: TournOp) -> bool {
    use TournOp::*;
    use TournamentSetting::*;
    match op {
        // Player commands
        AddDeck(..) => true,
        ConfirmResult(..) => true,
        DropPlayer(..) => true,
        RecordResult(..) => true,
        SetGamerTag(..) => true,
        RegisterPlayer(..) => true,
        RemoveDeck(..) => true,
        ReadyPlayer(..) => true,
        UnReadyPlayer(..) => true,
        // Admin commands
        Create(..) => true,
        AdminAddDeck(..) => true,
        AdminConfirmResult(..) => true,
        AdminDropPlayer(..) => true,
        AdminRecordResult(..) | AdminOverwriteResult(..) => true,
        AdminRegisterPlayer(..) => true,
        RegisterGuest(..) => true,
        RemoveRound(..) => true,
        CreateRound(..) => true,
        Cut(..) => true,
        End(..) | Cancel(..) => true,
        Freeze(..) => true,
        Thaw(..) => true,
        PairRound(..) => true,
        PrunePlayers(..) => true,
        Start(..) => true,
        TimeExtension(..) => true,
        GiveBye(..) => true,
        UpdateReg(..) => true,
        // Settings... This covers the admin commands
        UpdateTournSetting(.., setting) => match setting {
            Format(..) => true,
            MinDeckCount(_) => true,
            MaxDeckCount(_) => true,
            RequireCheckIn(..) => true,
            RequireDeckReg(..) => true,
            PairingSetting(setting) => {
                use squire_lib::settings::PairingSetting::*;
                match setting {
                    MatchSize(..) => true,
                    RepairTolerance(..) => true,
                    Algorithm(alg) => {
                        use squire_lib::pairings::PairingAlgorithm::*;
                        match alg {
                            Greedy => true,
                        }
                    }
                    Swiss(setting) => {
                        use squire_lib::settings::SwissPairingsSetting::*;
                        match setting {
                            DoCheckIns(..) => true,
                        }
                    }
                    Fluid(setting) => {
                        use squire_lib::settings::FluidPairingsSetting::*;
                        match setting {}
                    }
                }
            }
            ScoringSetting(setting) => {
                use squire_lib::settings::ScoringSetting::*;
                match setting {
                    Standard(setting) => {
                        use squire_lib::settings::StandardScoringSetting::*;
                        match setting {
                            MatchWinPoints(..) => true,
                            MatchDrawPoints(..) => true,
                            MatchLossPoints(..) => true,
                            GameWinPoints(..) => true,
                            GameDrawPoints(..) => true,
                            GameLossPoints(..) => true,
                            ByePoints(..) => true,
                            IncludeByes(..) => true,
                            IncludeMatchPoints(..) => true,
                            IncludeGamePoints(..) => true,
                            IncludeMwp(..) => true,
                            IncludeGwp(..) => true,
                            IncludeOppMwp(..) => true,
                            IncludeOppGwp(..) => true,
                        }
                    }
                }
            }
        },
    }
}

fn check_tourn_settings(setting: TournamentSetting) -> bool {
    use TournamentSetting::*;
    match setting {
        Format(..) => true,
        MinDeckCount(_) => true,
        MaxDeckCount(_) => true,
        RequireCheckIn(..) => true,
        RequireDeckReg(..) => true,
        PairingSetting(setting) => {
            use squire_lib::settings::PairingSetting::*;
            match setting {
                MatchSize(..) => true,
                RepairTolerance(..) => true,
                Algorithm(alg) => {
                    use squire_lib::pairings::PairingAlgorithm::*;
                    match alg {
                        Greedy => true,
                    }
                }
                Swiss(setting) => {
                    use squire_lib::settings::SwissPairingsSetting::*;
                    match setting {
                        DoCheckIns(..) => true,
                    }
                }
                Fluid(setting) => {
                    use squire_lib::settings::FluidPairingsSetting::*;
                    match setting {}
                }
            }
        }
        ScoringSetting(setting) => {
            use squire_lib::settings::ScoringSetting::*;
            match setting {
                Standard(setting) => {
                    use squire_lib::settings::StandardScoringSetting::*;
                    match setting {
                        MatchWinPoints(..) => true,
                        MatchDrawPoints(..) => true,
                        MatchLossPoints(..) => true,
                        GameWinPoints(..) => true,
                        GameDrawPoints(..) => true,
                        GameLossPoints(..) => true,
                        ByePoints(..) => true,
                        IncludeByes(..) => true,
                        IncludeMatchPoints(..) => true,
                        IncludeGamePoints(..) => true,
                        IncludeMwp(..) => true,
                        IncludeGwp(..) => true,
                        IncludeOppMwp(..) => true,
                        IncludeOppGwp(..) => true,
                    }
                }
            }
        }
    }
}
