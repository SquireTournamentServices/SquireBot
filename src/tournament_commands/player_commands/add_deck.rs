use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_core::{
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

#[command("add-deck")]
#[usage("<deck name>, <deck list/url>, [tournament name]")]
#[example("'SomeDeck', https://moxfield.com/decks/qwertyuiop/")]
#[description("Submits a deck.")]
async fn add_deck(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let name_and_id = data
        .get::<TournamentNameAndIDMapContainer>()
        .unwrap()
        .read()
        .await;
    let ids = data
        .get::<GuildAndTournamentIDMapContainer>()
        .unwrap()
        .read()
        .await;
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
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
    let tourn_id = match player_tourn_resolver(
        ctx,
        msg,
        tourn_name,
        all_tourns,
        ids.get_left_iter(&msg.guild_id.unwrap()).unwrap(),
    )
    .await
    {
        None => {
            return Ok(());
        }
        Some(id) => id,
    };
    let mut tourn = spin_mut(all_tourns, &tourn_id).await.unwrap();
    let plyr_id = match tourn.players.get_right(&msg.author.id) {
        Some(id) => PlayerIdentifier::Id(id.clone()),
        None => {
            msg.reply(&ctx.http, "You are not registered for that tournament.")
                .await?;
            return Ok(());
        }
    };
    let card_coll = data.get::<CardCollectionContainer>().unwrap().read().await;
    let deck = if let Some(deck) = card_coll.import_deck(raw_deck.clone()).await {
        deck
    } else if let Some(deck) = card_coll.import_deck(raw_deck).await {
        deck
    } else {
        msg.reply(&ctx.http, "Unable to create a deck from this.")
            .await?;
        return Ok(());
    };
    if let Err(err) = tourn
        .tourn
        .apply_op(TournOp::AddDeck(plyr_id, deck_name, deck))
    {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Deck successfully added!").await?;
    }
    Ok(())
}
