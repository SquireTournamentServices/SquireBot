use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

use crate::model::{
    containers::{
        GuildAndTournamentIDMapContainer, TournamentMapContainer, TournamentNameAndIDMapContainer,
    },
    guild_tournament::GuildTournament,
};

use crate::utils::error_to_reply::error_to_reply;
use crate::utils::spin_lock::spin_mut;
use crate::utils::tourn_resolver::{admin_tourn_id_resolver, user_id_resolver};
use squire_lib::operations::TournOp;

#[command("register")]
#[only_in(guild)]
#[sub_commands("guest")]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<player name/mention>, [tournament name]")]
#[example("'SomePlayer'")]
#[example("@SomePlayer")]
#[description("Registers a player on their behalf.")]
async fn register(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let user_id = match user_id_resolver(ctx, msg, &raw_user_id).await {
        Some(id) => id,
        None => {
            msg.reply(
                &ctx.http,
                "That person could not be found.",
            )
            .await?;
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

    let mut tourn = spin_mut(&all_tourns, &tourn_id).await.unwrap();

    if let Err(err) = tourn.add_player(user_id.0.to_string(), user_id) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        let _ = msg
            .guild(ctx)
            .unwrap()
            .member(ctx, user_id)
            .await
            .unwrap()
            .add_role(ctx, tourn.tourn_role.id)
            .await;
        msg.reply(&ctx.http, "Player successfully registered!")
            .await?;
    }
    Ok(())
}

#[command("guest")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<player name>, [tournament name]")]
#[example("'SomePlayer'")]
#[description("Registers a player that isn't on Discord.")]
async fn guest(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let user_name = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(
                &ctx.http,
                "Please include the player's name.",
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

    let mut tourn = spin_mut(&all_tourns, &tourn_id).await.unwrap();

    if let Err(err) = tourn.add_guest(user_name) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Player successfully registered!")
            .await?;
    }
    Ok(())
}
