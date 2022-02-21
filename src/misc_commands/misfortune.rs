use crate::model::misfortune::*;

use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("misfortune")]
#[sub_commands(create)]
#[min_args(1)]
#[max_args(1)]
#[description("Helps you resolve Wheel of Misfortune.")]
async fn misfortune(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let mis_players = data.get::<MisfortunePlayerContainer>().unwrap();
    if let Some(r_id) = mis_players.get(&msg.author.id) {
        let misfortunes = data.get::<MisfortuneContainer>().unwrap();
        let mut mis = misfortunes.get_mut(&r_id).unwrap();
        if let Ok(val) = args.rest().parse::<u64>() {
            let origin = ctx.http.get_message(mis.get_channel().0, mis.get_message().0).await?;
            // We have the message, so we know that it is safe to change the misfortune
            let done = mis.add_response(msg.author.id.clone(), val);
            if done {
                origin.reply(&ctx.http, format!("Here is the result of your Misfortune:{}", mis.pretty_str())).await?;
                drop(mis);
                misfortunes.remove(&r_id);
            }
        } else {
            msg.reply(&ctx.http, "Please give a valid number.").await?;
        }
    } else {
        msg.reply(&ctx.http, "You don't have a waiting misfortune.").await?;
    }
    Ok(())
}

#[command("create")]
#[only_in(guild)]
#[min_args(0)]
#[max_args(1)]
#[description("Start resolving Wheel of Misfortune.")]
async fn create(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}
