use std::io::{self, Write};

use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
    CacheAndHttp,
};
use tempfile::tempfile;

use squire_lib::{
    operations::TournOp, player_registry::PlayerIdentifier, round_registry::RoundIdentifier,
};

use crate::{
    model::containers::{
        GuildAndTournamentIDMapContainer, TournamentMapContainer, TournamentNameAndIDMapContainer,
    },
    utils::{
        error_to_reply::error_to_reply,
        spin_lock::spin_mut,
        stringify::bool_from_string,
        tourn_resolver::{admin_tourn_id_resolver, player_name_resolver, user_id_resolver},
    },
};

#[command("raw-standings")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<top N>, [tournament name]")]
#[example("25")]
#[description("Delivers a txt file with simplified standings.")]
async fn raw_standings(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let raw_count = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(
                &ctx.http,
                "Please include a count for the number of players shown or 'all'.",
            )
            .await?;
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
    let mut tourn = spin_mut(all_tourns, &tourn_id).await.unwrap();
    let standings = tourn.tourn.get_standings();
    let count = match raw_count.as_str() {
        "all" | "All" | "a" | "A" => standings.scores.len(),
        _ => {
            if let Ok(n) = raw_count.parse::<usize>() {
                n
            } else {
                msg.reply(&ctx.http, r#"Please specify a max count or the word "all""#)
                    .await?;
                return Ok(());
            }
        }
    };
    let mut output = tempfile().unwrap();
    for (i, (id, s)) in standings.scores.iter().enumerate() {
        if i > count {
            break;
        }
        let _ = writeln!(
            output,
            "{i}) {}",
            player_name_resolver(id.clone(), &tourn.players, &tourn.tourn)
        );
    }
    let to_send = tokio::fs::File::from_std(output);
    let channel = msg.channel(&ctx.http).await?;
    match channel {
        Channel::Guild(c) => {
            c.send_message(&ctx.http, |m| {
                m.content("Here are the top {} players").files(
                    [AttachmentType::File {
                        file: &to_send,
                        filename: String::from("standings.txt"),
                    }]
                    .into_iter(),
                )
            })
            .await?;
        }
        _ => {
            unreachable!("How did you get here?");
        }
    }
    Ok(())
}
