/// This module does nothing of direct substance. Rather, it softly ensures that, when not compiling in
/// release mode, the there are commands for each tournament operation, tournament setting, and any
/// other input enums from squire_lib.

use squire_lib::{operations::TournOp, settings::{TournamentSetting, PairingSetting, FluidPairingsSetting, ScoringSetting, StandardScoringSetting, SwissPairingsSetting}};

fn check_tourn_ops(op: TournOp) -> bool {
    use TournOp::*;
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
        AdminRecordResult(..) => true,
        AdminRegisterPlayer(..) => true,
        CreateRound(..) => true,
        Cut(..) => true,
        End(..) => true,
        Freeze(..) => true,
        Thaw(..) => true,
        GiveBye(..) => true,
        PairRound(..) => true,
        PruneDecks(..) => true,
        PrunePlayers(..) => true,
        Start(..) => true,
        TimeExtension(..) => true,
        GiveBye(..) => true,
    }
}

fn check_tourn_settings(setting: TournamentSetting) -> bool {
    use TournamentSetting::*;
    match setting {
    }
}

fn check_pairing_settings(setting: PairingSetting) -> bool {
    use PairingSetting::*;
    match setting {
    }
}

fn check_swiss_settings(setting: SwissPairingsSetting) -> bool {
    use SwissPairingsSetting::*;
    match setting {
    }
}

fn check_fluid_settings(setting: FluidPairingsSetting) -> bool {
    use FluidPairingsSetting::*;
    match setting {
    }
}

fn check_scoring_settings(setting: ScoringSetting) -> bool {
    use ScoringSetting::*;
    match setting {
    }
}

fn check_standard_scoring_settings(setting: StandardScoringSetting) -> bool {
    use StandardScoringSetting::*;
    match setting {
    }
}
