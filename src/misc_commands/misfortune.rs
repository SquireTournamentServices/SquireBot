use std::collections::HashSet;

use crate::{
    model::{
        containers::{
            GuildAndTournamentIDMapContainer, MisfortuneMapContainer, MisfortuneUserMapContainer,
            TournamentMapContainer, TournamentNameAndIDMapContainer,
        },
        misfortune::*,
    },
    utils::tourn_resolver::tourn_id_resolver,
};

use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_core::{
    player_registry::PlayerIdentifier,
    round::{Round, RoundId},
    round_registry::RoundIdentifier,
    tournament::TournamentId,
};

#[command("misfortune")]
#[sub_commands(create)]
#[min_args(1)]
#[max_args(1)]
#[description("Helps you resolve Wheel of Misfortune.")]
async fn misfortune(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    /* Old version
    let data = ctx.data.read().await;
    let mis_players = data.get::<MisfortunePlayerMapContainer>().unwrap();
    if let Some(r_id) = mis_players.get(&msg.author.id) {
        let misfortunes = data.get::<MisfortuneMapContainer>().unwrap();
        let mut mis = misfortunes.get_mut(&r_id).unwrap();
        if let Ok(val) = args.rest().parse::<u64>() {
            let origin = ctx
                .http
                .get_message(mis.get_channel().0, mis.get_message().0)
                .await?;
            // We have the message, so we know that it is safe to change the misfortune
            let done = mis.add_response(msg.author.id.clone(), val);
            if done {
                origin
                    .reply(
                        &ctx.http,
                        format!("Here is the result of your Misfortune:{}", mis.pretty_str()),
                    )
                    .await?;
                for p in &mis.players {
                    mis_players.remove(p);
                }
                drop(mis);
                misfortunes.remove(&r_id);
            }
        } else {
            msg.reply(&ctx.http, "Please give a valid number.").await?;
        }
    } else {
        msg.reply(&ctx.http, "You don't have a waiting misfortune.")
            .await?;
    }
    Ok(())
    */
    todo!()
}

#[command("create")]
#[only_in(guild)]
#[min_args(0)]
#[max_args(1)]
#[description("Start resolving Wheel of Misfortune.")]
async fn create(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    /* Old version */
    let data = ctx.data.read().await;
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
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
    let given_name = args.rest();
    let id_iter = gld_tourns
        .get_left_iter(&msg.guild_id.unwrap())
        .unwrap()
        .cloned();
    let tourn_id = match tourn_id_resolver(ctx, msg, given_name, &name_and_id, id_iter).await {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let tourn = all_tourns.get(&tourn_id).unwrap();
    let plyr_id = match tourn.get_player_id(&msg.author.id) {
        Some(id) => PlayerIdentifier::Id(id),
        None => {
            let _ = msg
                .reply(&ctx.http, "You are not registered for that tournament.")
                .await;
            return Ok(());
        }
    };
    let mut rounds: Vec<Round> = tourn
        .tourn
        .get_player_rounds(&plyr_id)
        .unwrap()
        .into_iter()
        .filter(|r| !r.is_certified())
        .collect();
    if rounds.is_empty() {
        msg.reply(&ctx.http, "You are not in an active match.")
            .await?;
        return Ok(());
    } else if rounds.len() > 1 {
        msg.reply(
            &ctx.http,
            "You are in multiple active matches. Please state the match number.",
        )
        .await?;
        return Ok(());
    }
    let round_id = rounds.pop().unwrap().id;
    let mut user_round_map = data
        .get::<MisfortuneUserMapContainer>()
        .unwrap()
        .write()
        .await;
    let round = tourn
        .tourn
        .get_round(&RoundIdentifier::Id(round_id.clone()))
        .unwrap();
    user_round_map.insert_right(round_id.clone());
    let mut mis = Misfortune::new(HashSet::new(), msg.channel_id, msg.id);
    for plyr in round.get_all_players() {
        let user = tourn.get_user_id(&plyr).unwrap();
        user_round_map.insert_left(user, &round_id);
        mis.players.insert(user);
        let _ = msg
            .guild(&ctx)
            .unwrap()
            .member(&ctx, user)
            .await
            .unwrap()
            .user
            .dm(&ctx, |m| {
                m.content("Enter in your misfortune number with `!misfortune`")
            })
            .await;
    }
    let misforunes = data.get::<MisfortuneMapContainer>().unwrap();
    misforunes.insert(round_id, mis);
    msg.reply(&ctx.http, "Respond to the DM to record your response.")
        .await?;
    Ok(())
}
