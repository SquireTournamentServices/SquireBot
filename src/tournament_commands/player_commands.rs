#![deny(unused)]
use std::collections::HashMap;

use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::Message,
    prelude::Context,
};

use squire_lib::{
    accounts::{SharingPermissions::Everything, SquireAccount},
    identifiers::PlayerId,
    operations::TournOp,
    round::RoundResult::*,
};

use crate::{
    model::{
        containers::{
            CardCollectionContainer, GuildAndTournamentIDMapContainer, TournamentMapContainer,
            TournamentNameAndIDMapContainer,
        },
        guild_tournament::{GuildTournamentAction, GuildTournamentAction::*},
    },
    utils::{spin_lock::spin_mut, tourn_resolver::player_tourn_resolver},
};

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
    let tourn_name = args.rest().to_string();
    let data = ctx.data.read().await;
    let card_coll = data.get::<CardCollectionContainer>().unwrap().read().await;
    match card_coll.import_deck(raw_deck.clone()).await {
        Some(deck) => {
            player_command(ctx, msg, tourn_name, move |p| {
                TournOp::AddDeck(p.into(), deck_name, deck).into()
            })
            .await
        }
        None => {
            msg.reply(&ctx.http, "Unable to create a deck from this.")
                .await?;
            return Ok(());
        }
    }
}

#[command("confirm-result")]
#[only_in(guild)]
#[usage("[tournament name]")]
#[description("Confirm the result of your match.")]
async fn confirm_result(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().to_string();
    player_command(ctx, msg, tourn_name, |p| {
        TournOp::ConfirmResult(p.into()).into()
    })
    .await
}

#[command("decklist")]
#[usage("[tournament name]")]
#[description("Prints out one of your decklists.")]
async fn decklist(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    match args.single_quoted::<String>() {
        Ok(deck_name) => {
            let tourn_name = args.rest().trim().to_string();
            player_command(ctx, msg, tourn_name, move |p| {
                ViewDecklist(p.into(), deck_name)
            })
            .await
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please include a deck name.").await?;
            Ok(())
        }
    }
}

#[command("decks")]
#[usage("[tournament name]")]
#[description("Prints out a summary of your decks.")]
async fn decks(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().to_string();
    player_command(ctx, msg, tourn_name, |p| ViewPlayerDecks(p.into())).await
}

#[command("drop")]
#[only_in(guild)]
#[usage("[tournament name]")]
#[description("Removes you from the tournament.")]
async fn drop(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().to_string();
    player_command(ctx, msg, tourn_name, |p| {
        TournOp::DropPlayer(p.into()).into()
    })
    .await
}

#[command("list")]
#[only_in(guild)]
#[description("Lists out all tournament in the server.")]
async fn list(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    /* Get references to needed data from context */
    let data = ctx.data.read().await;
    let name_and_id = data
        .get::<TournamentNameAndIDMapContainer>()
        .unwrap()
        .read()
        .await;
    let gld_tourns = data
        .get::<GuildAndTournamentIDMapContainer>()
        .unwrap()
        .read()
        .await;

    let response: String = match gld_tourns.get_left_iter(&msg.guild_id.unwrap()) {
        None => "There are no tournaments being held in this server.".into(),
        Some(id_iter) => id_iter
            .map(|tourn| name_and_id.get_left(&tourn).unwrap().as_str())
            .collect(),
    };
    msg.reply(&ctx.http, response).await?;
    Ok(())
}

#[command("match-result")]
#[only_in(guild)]
#[sub_commands(draws)]
#[usage("<# of wins>, [tournament name]")]
#[example("2")]
#[description("Submit the result of a match.")]
async fn match_result(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    match args.single::<u8>() {
        Ok(wins) => {
            let tourn_name = args.rest().trim().to_string();
            player_command(ctx, msg, tourn_name, move |p| {
                TournOp::RecordResult(p.into(), Wins(p, wins)).into()
            })
            .await
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please include the number of times you won.")
                .await?;
            Ok(())
        }
    }
}

#[command("draws")]
#[only_in(guild)]
#[usage("<# of draws>, [tournament name]")]
#[example("2")]
#[description("Submit the number of draws of a match.")]
async fn draws(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    match args.single::<u8>() {
        Ok(draws) => {
            let tourn_name = args.rest().trim().to_string();
            player_command(ctx, msg, tourn_name, move |p| {
                TournOp::RecordResult(p.into(), Draw(draws)).into()
            })
            .await
        }
        Err(_) => {
            msg.reply(
                &ctx.http,
                "Please include the number of draws in your match.",
            )
            .await?;
            Ok(())
        }
    }
}

#[command("name")]
#[only_in(guild)]
#[usage("[tournament name]")]
#[description("Adjust your name in the tournament.")]
async fn name(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    match args.single_quoted::<String>() {
        Ok(gamer_tag) => {
            let tourn_name = args.rest().trim().to_string();
            player_command(ctx, msg, tourn_name, move |p| {
                TournOp::SetGamerTag(p.into(), gamer_tag).into()
            })
            .await
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please include your gamer tag.")
                .await?;
            Ok(())
        }
    }
}

#[command("ready")]
#[only_in(guild)]
#[aliases("lfg")]
#[usage("[tournament name]")]
#[description("Adds you to the match-making queue.")]
async fn ready(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().to_string();
    player_command(ctx, msg, tourn_name, |p| {
        TournOp::ReadyPlayer(p.into()).into()
    })
    .await
}

#[command("unready")]
#[only_in(guild)]
#[aliases("leave-lfg")]
#[usage("[tournament name]")]
#[description("Removes you from the match-making queue.")]
async fn unready(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().to_string();
    player_command(ctx, msg, tourn_name, |p| {
        TournOp::UnReadyPlayer(p.into()).into()
    })
    .await
}

#[command("register")]
#[only_in(guild)]
#[usage("[tournament name]")]
#[description("Register for a tournament.")]
async fn register(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().to_string();
    player_command(ctx, msg, tourn_name, |p| {
        let account = SquireAccount {
            user_name: p.to_string(),
            display_name: p.to_string(),
            gamer_tags: HashMap::new(),
            user_id: (*p).into(),
            permissions: Everything,
        };
        TournOp::RegisterPlayer(account).into()
    })
    .await
}

#[command("remove-deck")]
#[only_in(guild)]
#[usage("<deck name>, [tournament name]")]
#[example("'SomeDeck'")]
#[description("Removes one of your decks.")]
async fn remove_deck(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().to_string();
    player_command(ctx, msg, tourn_name, |p| {
        TournOp::DropPlayer(p.into()).into()
    })
    .await
}

/// Handles 90% of a player command what performs an action
pub async fn player_command<F>(
    ctx: &Context,
    msg: &Message,
    tourn_name: String,
    f: F,
) -> CommandResult
where
    F: FnOnce(PlayerId) -> GuildTournamentAction,
{
    let data = ctx.data.read().await;
    let ids = data
        .get::<GuildAndTournamentIDMapContainer>()
        .unwrap()
        .read()
        .await;
    let all_tourns = data.get::<TournamentMapContainer>().unwrap().read().await;
    // Resolve the tournament id
    let tourn_id = match player_tourn_resolver(
        ctx,
        msg,
        tourn_name,
        &all_tourns,
        ids.get_left_iter(&msg.guild_id.unwrap()).unwrap(),
    )
    .await?
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = spin_mut(&all_tourns, &tourn_id).await.unwrap();
    match tourn.players.get_right(&msg.author.id) {
        Some(id) => {
            let id = id.clone().into();
            tourn.take_action(ctx, msg, f(id))?;
        }
        None => {
            msg.reply(&ctx.http, "You are not registered for that tournament.")
                .await?;
        }
    }
    Ok(())
}
