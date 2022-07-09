use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;
use squire_lib::operations::TournOp;

use crate::utils::spin_lock::spin_mut;
use crate::{
    model::containers::{
        GuildAndTournamentIDMapContainer, TournamentMapContainer, TournamentNameAndIDMapContainer,
    },
    utils::{error_to_reply::error_to_reply, tourn_resolver::admin_tourn_id_resolver},
};

#[command("freeze")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("[tournament name]")]
#[example("freeze")]
#[description("Pauses a tournament.")]
async fn freeze(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    // Freeze the tournament
    let mut tourn = spin_mut(all_tourns, &tourn_id).await.unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::Freeze()) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        msg.reply(&ctx.http, "Tournament successfully frozen!")
            .await?;
    }
    Ok(())
}

#[command("thaw")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("[tournament name]")]
#[example("thaw")]
#[description("Resumes a frozen a tournament.")]
async fn thaw(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    // Freeze the tournament
    let mut tourn = spin_mut(all_tourns, &tourn_id).await.unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::Thaw()) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Tournament successfully thawed!")
            .await?;
    }
    Ok(())
}
