use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_lib::{
    operations::TournOp, player_registry::PlayerIdentifier, tournament::TournamentId,
};
use uuid::Uuid;

use crate::{
    model::containers::{
        CardCollectionContainer, GuildAndTournamentIDMapContainer, TournamentMapContainer,
        TournamentNameAndIDMapContainer,
    },
    utils::{
        error_to_reply::error_to_reply,
        spin_lock::{spin, spin_mut},
        tourn_resolver::{admin_tourn_id_resolver, player_tourn_resolver, user_id_resolver},
    },
};

use super::common_command::player_command;

#[command("add-deck")]
#[usage("<deck name>, <deck list/url>, [tournament name]")]
#[example("'SomeDeck', https://moxfield.com/decks/qwertyuiop/")]
#[description("Submits a deck.")]
async fn add_deck(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let deck_name = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please include a deck name.").await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let raw_deck = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please include a deck.").await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let tourn_name = args.rest().trim().to_string();
    match player_command(ctx, msg, tourn_name, move |tourn, plyr|{ async move
        {
        let data = ctx.data.read().await;
        let card_coll = data.get::<CardCollectionContainer>().unwrap().read().await;
        if let Some(deck) = card_coll.import_deck(raw_deck.clone()).await {
            tourn.update_status = true;
            Some(TournOp::AddDeck(plyr, deck_name, deck))
        } else {
            let _ = msg
                .reply(&ctx.http, "Unable to create a deck from this.")
                .await;
            None
        }
    } })
    .await
    {
        None => Ok(()),
        Some(Err(err)) => {
            error_to_reply(ctx, msg, err).await?;
            Ok(())
        }
        Some(Ok(_)) => {
            msg.reply(&ctx.http, "Deck successfully added!").await?;
            Ok(())
        }
    }
}
