use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_lib::{operations::TournOp, player_registry::PlayerIdentifier};

use crate::{
    model::containers::{
        GuildAndTournamentIDMapContainer, TournamentMapContainer, TournamentNameAndIDMapContainer,
    },
    utils::{
        error_to_reply::error_to_reply,
        spin_lock::spin_mut,
        tourn_resolver::{admin_tourn_id_resolver, user_id_resolver},
    },
};

#[command("remove-deck")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<player name/mention>, <deck name>, [tournament name]")]
#[example("'SomePlayer', https://moxfield.com/decks/qwertyuiop/")]
#[example("@SomePlayer, https://moxfield.com/decks/qwertyuiop/")]
#[description("Removes a deck on behave of a player.")]
async fn remove_deck(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap().read().await;
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
    let deck_name = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please include a deck name.").await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = spin_mut(&all_tourns, &tourn_id).await.unwrap();
    let plyr_id = match user_id_resolver(ctx, msg, &raw_user_id).await {
        Some(user_id) => {
            match tourn.players.get_right(&user_id) {
                Some(id) => id.clone().into(),
                None => {
                    msg.reply(
                        &ctx.http,
                        "That player is not registered for the tournament.",
                    )
                    .await?;
                    return Ok(());
                }
            }
        },
        None => {
            match tourn.guests.get_right(&raw_user_id) {
                Some(id) => id.clone().into(),
                None => {
                    msg.reply(
                        &ctx.http,
                        "That guest is not registered for the tournament. You may have mistyped their name.",
                    )
                    .await?;
                    return Ok(());
                }
            }
        }
    };
    if let Err(err) = tourn
        .tourn
        .apply_op(TournOp::RemoveDeck(plyr_id, deck_name))
    {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Deck successfully removed!").await?;
    }
    Ok(())
}
