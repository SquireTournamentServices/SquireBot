use std::collections::HashSet;

use crate::model::{
    containers::{MisfortuneMapContainer, MisfortunePlayerMapContainer, TournamentMapContainer},
    lookup_error::LookupError,
    misfortune::*,
};

use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_core::{
    player_registry::PlayerIdentifier, round::RoundId, round_registry::RoundIdentifier,
    tournament::TournamentId,
};

#[command("misfortune")]
#[sub_commands(create)]
#[min_args(1)]
#[max_args(1)]
#[description("Helps you resolve Wheel of Misfortune.")]
async fn misfortune(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
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
}

#[command("create")]
#[only_in(guild)]
#[min_args(0)]
#[max_args(1)]
#[description("Start resolving Wheel of Misfortune.")]
async fn create(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    // TODO: Make resolver for user to tournament mapping
    // let data = ctx.data.read().await;
    // let all_tourns = data.get::<TournamentContainer>().unwrap();
    // let gld_tourns = data.get::<GuildTournamentsContainer>().unwrap();
    // let local_tourns = gld_tourns.get(&msg.guild_id.unwrap()).unwrap();
    let data = ctx.data.read().await;
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let gld_tourns = data.get::<GuildTournamentsMapContainer>().unwrap();
    let local_tourns = gld_tourns.get(&msg.guild_id.unwrap()).unwrap();
    let name_and_tourn = user_to_tourn(all_tourns, &local_tourns, &ctx.http, &msg, &args).await?;
    // Do some tournament queries
    let p_id = name_and_tourn.value().get_player_id(msg.author.id).unwrap();
    let tourn_id = name_and_tourn.value().get_id();
    let tourn = all_tourns.get_tourn(TournIdentifier::Id(tourn_id)).unwrap();
    let r_id = match tourn.get_player_round(PlayerIdentifier::Id(p_id)) {
        Err(e) => {
            msg.reply(&ctx.http, "You aren't in an active match.")
                .await?;
            Err(e)?
        }
        Ok(r) => r,
    };
    let round = tourn.value().get_round(RoundIdentifier::Id(r_id)).unwrap();
    let players: HashSet<UserId> = round
        .get_all_players()
        .iter()
        .filter_map(|p| name_and_tourn.value().get_user_id(p.clone()))
        .collect();
    let player_misfortunes = data.get::<MisfortunePlayerContainer>().unwrap();
    for p in &players {
        match ctx.http.get_user(p.0).await {
            Err(e) => {
                // This shouldn't happen...
                msg.reply(
                    &ctx.http,
                    "There was an error in finding one of your opponents.",
                )
                .await?;
                Err(e)?
            }
            Ok(u) => {
                u.dm(&ctx.http, |m| {
                    m.content(
                        "Please use the `!misfortune` command to resolve the Wheel of Misfortune.",
                    )
                })
                .await?;
            }
        }
        player_misfortunes.insert(p.clone(), r_id.clone());
    }
    let mis = Misfortune::new(players, msg.channel_id, msg.id);
    let all_misfortunes = data.get::<MisfortuneContainer>().unwrap();
    all_misfortunes.insert(r_id, mis);
    msg.reply(&ctx.http, "Respond with your number via DM!")
        .await?;
    Ok(())
}
