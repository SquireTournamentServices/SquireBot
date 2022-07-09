use itertools::Itertools;
use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_core::{operations::TournOp, player::PlayerStatus, player_registry::PlayerIdentifier};

use crate::{
    model::containers::{
        CardCollectionContainer, GuildAndTournamentIDMapContainer, TournamentMapContainer,
        TournamentNameAndIDMapContainer,
    },
    utils::{
        error_to_reply::error_to_reply,
        spin_lock::spin,
        tourn_resolver::{admin_tourn_id_resolver, user_id_resolver},
    },
};

#[command("profile")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<player name/mention>, [tournament name]")]
#[example("'SomePlayer'")]
#[example("@SomePlayer")]
#[description("Prints out the profile of a player.")]
async fn profile(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let tourn = spin(all_tourns, &tourn_id).await.unwrap();
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
    let rounds = tourn.tourn.get_player_rounds(&plyr_id).unwrap();
    match msg.channel(&ctx.http).await.unwrap() {
        Channel::Guild(c) => {
            c.send_message(&ctx.http, |m| {
                m.embed(|e| {
                    if let Some(tag) = plyr.game_name {
                        e.field("Game Tag:", tag, false);
                    }
                    e.title(format!("<@{}> Profile", user_id))
                        .field(
                            "Status:",
                            match plyr.status {
                                PlayerStatus::Registered => "Registered",
                                PlayerStatus::Dropped => "Dropped",
                            },
                            false,
                        )
                        .field("Decks:", plyr.decks.keys().join("\n"), false)
                        .field(
                            "Matches:",
                            rounds
                                .iter()
                                .map(|r| format!("Match #{}", r.match_number))
                                .join("\n"),
                            false,
                        )
                })
            })
            .await?;
        }
        _ => {
            unreachable!("Can't send message from non guild channel.");
        }
    }
    Ok(())
}
