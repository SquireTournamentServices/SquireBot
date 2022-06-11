use serenity::{client::Context, framework::standard::CommandResult, model::channel::Message};
use squire_core::swiss_pairings::TournamentError;

// A function for deliverying canned responses based on a TournamentError
pub async fn error_to_reply(ctx: &Context, msg: &Message, err: TournamentError) -> CommandResult {
    use squire_core::error::TournamentError::*;
    match err {
        IncorrectStatus => {
            msg.reply(
                &ctx.http,
                "That tournament isn't taking new players right now.",
            )
            .await?;
        }
        RegClosed => {
            msg.reply(&ctx.http, "Registertion is closed for that tournament.")
                .await?;
        }
        PlayerLookup => {
            msg.reply(&ctx.http, "That person is not a player in that tournament.")
                .await?;
        }
        RoundLookup => {
            msg.reply(&ctx.http, "That round could not be found.")
                .await?;
        }
        DeckLookup => {
            msg.reply(&ctx.http, "That deck could not be found.")
                .await?;
        }
        PlayerNotInRound => {
            msg.reply(&ctx.http, "That player isn't in that round.")
                .await?;
        }
        NoActiveRound => {
            msg.reply(&ctx.http, "That player isn't in an active round.")
                .await?;
        }
        InvalidBye => {
            msg.reply(&ctx.http, "There must be exactly one player in a bye.")
                .await?;
        }
        ActiveMatches => {
            msg.reply(
                &ctx.http,
                "That tournament has outstanding matches. They need to finish first.",
            )
            .await?;
        }
        PlayerNotCheckedIn => {
            // Not sure what to say here...
            msg.reply(
                &ctx.http,
                "That tournament has an incompatible pairing system for that to work.",
            )
            .await?;
        }
        IncompatiblePairingSystem => {
            msg.reply(
                &ctx.http,
                "That tournament has an incompatible pairing system for that to work.",
            )
            .await?;
        }
        IncompatibleScoringSystem => {
            msg.reply(
                &ctx.http,
                "That tournament has an incompatible scoring system for that to work.",
            )
            .await?;
        }
    };
    Ok(())
}
