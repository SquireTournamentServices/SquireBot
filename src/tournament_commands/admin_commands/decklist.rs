use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_core::{operations::TournOp, player_registry::PlayerIdentifier};

use crate::{
    model::containers::{
        GuildAndTournamentIDMapContainer, TournamentMapContainer, TournamentNameAndIDMapContainer,
    },
    utils::{
        error_to_reply::error_to_reply,
        sort_deck::TypeSortedDeck,
        spin_lock::spin_mut,
        tourn_resolver::{admin_tourn_id_resolver, user_id_resolver},
    },
};

#[command("decklist")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<player name/mention>, <deck name>, [tournament name]")]
#[example("'SomePlayer', SomeDeck")]
#[example("@SomePlayer, 'SomeDeck'")]
#[description("Prints out the decklist of a player.")]
async fn decklist(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let raw_user_id = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(
                &ctx.http,
                "Please include a player, either by name or mention.",
            )
            .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let user_id = match user_id_resolver(ctx, msg, &raw_user_id).await {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let deck_name = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please include a deck name.").await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    if deck_name.is_empty() {
        msg.reply(&ctx.http, "Please include the name of the deck.")
            .await?;
        return Ok(());
    }
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = spin_mut(all_tourns, &tourn_id).await.unwrap();
    let plyr_id = match tourn.players.get_right(&user_id) {
        Some(id) => PlayerIdentifier::Id(id.clone()),
        None => {
            msg.reply(
                &ctx.http,
                "That player is not registered for the tournament.",
            )
            .await?;
            return Ok(());
        }
    };
    let plyr = tourn.tourn.get_player(&plyr_id).unwrap();
    match plyr.get_deck(&deck_name) {
        Some(deck) => {
            let sorted_deck = TypeSortedDeck::from(deck);
            match msg.channel(&ctx.http).await? {
                Channel::Guild(channel) => {
                    channel
                        .send_message(&ctx.http, |m| {
                            m.embed(|e| {
                                sorted_deck
                                    .populate_embed(e)
                                    .title(format!("<@{user_id}>'s Deck: {deck_name}"))
                            })
                        })
                        .await?;
                }
                _ => {
                    unreachable!("This command can only be sent from guild channels.")
                }
            }
        }
        None => {
            msg.reply(&ctx.http, "That player doesn't have a deck called that.")
                .await?;
        }
    }
    Ok(())
}
