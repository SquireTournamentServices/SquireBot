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
        tourn_resolver::{admin_tourn_id_resolver, user_id_resolver},
    },
};

#[command("give-bye")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[description("Gives a player a bye.")]
async fn give_bye(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let raw_user_id = args.single_quoted::<String>().unwrap();
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
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
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
    if let Err(err) = tourn.tourn.apply_op(TournOp::GiveBye(plyr_id)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        tourn.update_standings = true;
        msg.reply(&ctx.http, "Bye successfully give!").await?;
    }
    Ok(())
}
