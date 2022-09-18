use serenity::{framework::standard::CommandResult, model::prelude::Message, prelude::Context};

use squire_lib::{
    error::TournamentError::{self, *},
    operations::TournOp::{self, *},
    round::RoundStatus::*,
    tournament::TournamentStatus::*,
};

pub async fn subcommand_default(ctx: &Context, msg: &Message, cmd: &str) -> CommandResult {
    msg.reply(
        &ctx.http,
        format!("Please specify a subcommand. If you're unsure, use `!sb-help {cmd}`."),
    )
    .await?;
    Ok(())
}

pub fn op_to_content(op: &TournOp) -> &'static str {
    match op {
        Create(..) => {
            unreachable!("You shouldn't be creating a tournament this way");
        }
        CheckIn(..) => "You successfully checked in!!",
        RegisterPlayer(..) => "You have been successfully registered!!",
        DropPlayer(..) => "You have been successfully dropped!!",
        RecordResult(..) => "Your result was successfully recorded!!",
        ConfirmResult(..) => "You have successfully confirmed the result of your match!!",
        AddDeck(..) => "You have successfully registered a deck!!",
        RemoveDeck(..) => "You have successfully removed a deck!!",
        SetGamerTag(..) => "You have successfully set your gamer tag!!",
        ReadyPlayer(..) => "You have successfully marked yourself as ready to play!!",
        UnReadyPlayer(..) => "You have successfully marked yourself as unready to play!!",
        RegisterGuest(..) => "You have successfully registered a player!!",
        AdminRegisterPlayer(..) => "You have successfully registed a player!!",
        AdminRecordResult(..) => {
            "You have successfully recorded that player's result of that match!!"
        }
        AdminConfirmResult(..) => {
            "You have successfully recorded that match's result for that player!!"
        }
        AdminAddDeck(..) => "You have successfully added a deck for that player!!",
        AdminRemoveDeck(..) => "You have successfully removed that deck from that player!!",
        AdminReadyPlayer(..) => "You have successfully marked that player as ready to play!!",
        AdminUnReadyPlayer(..) => "You have successfully marked that player as not ready to play!!",
        TimeExtension(..) => "You have successfully given that match a time extension!!",
        UpdateReg(..) => "You have successfully updated the registration status!!",
        Start(..) => "You have successfully started the tournament!!",
        Freeze(..) => "You have successfully frozen the tournament!!",
        Thaw(..) => "You have successfully thawed the tournament!!",
        End(..) => "You have successfully ended the tournament!!",
        Cancel(..) => "You have successfully cancelled the tournament!!",
        AdminOverwriteResult(..) => "You have successfully overwriten the result of that match!!",
        RegisterJudge(..) => "You have successfully registered that person as a judge!!",
        RegisterAdmin(..) => "You have successfully registered that person as an admin!!",
        AdminDropPlayer(..) => "You have successfully dropped that player!!",
        RemoveRound(..) => "You have successfully removed that round!!",
        UpdateTournSetting(..) => "You have successfully updated that tournament setting!!",
        GiveBye(..) => "You have successfully given a bye to that player!!",
        CreateRound(..) => "You have successfully created a match for those players!!",
        PairRound(..) => "You have successfully paired the next round!!",
        Cut(..) => "You have successfully such to the top of the tournament!!",
        PruneDecks(..) => "You have successfully pruned excess decks from players!!",
        PrunePlayers(..) => "You have successfully pruned excess players!!",
    }
}

pub fn error_to_content(err: TournamentError) -> &'static str {
    match err {
        IncorrectStatus(s) => match s {
            Planned => "That tournament hasn't started yet.",
            Started => "That tournament has already started.",
            Frozen => "That tournament is currently frozen.",
            Ended => "That tournament has already ended.",
            Cancelled => "That tournament has been cancelled.",
        },
        IncorrectRoundStatus(s) => match s {
            Open => "That round is active.",
            Certified => "That round is certified.",
            Uncertified => "That round is partial certified.",
            Dead => "That round has been removed.",
        },
        RoundConfirmed => "That round has already been certified.",
        InvalidDeckCount => "The minimum deck count must be less than the maximum count.",
        OfficalLookup => "That person could not be found as an official.",
        RegClosed => "Registertion is closed for that tournament.",
        PlayerLookup => "That person is not a player in that tournament.",
        RoundLookup => "That round could not be found.",
        DeckLookup => "That deck could not be found.",
        PlayerNotInRound => "That player isn't in that round.",
        NoActiveRound => "That player isn't in an active round.",
        InvalidBye => "There must be exactly one player in a bye.",
        ActiveMatches => "That tournament has outstanding matches. They need to finish first.",
        PlayerNotCheckedIn => "You are not checked in.",
        IncompatiblePairingSystem => {
            "That tournament has an incompatible pairing system for that to work."
        }
        IncompatibleScoringSystem => {
            "That tournament has an incompatible scoring system for that to work."
        }
    }
}
