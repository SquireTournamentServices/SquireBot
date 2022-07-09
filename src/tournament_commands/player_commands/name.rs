use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_core::{operations::TournOp, player_registry::PlayerIdentifier};

use crate::{
    model::containers::{
        CardCollectionContainer, GuildAndTournamentIDMapContainer, TournamentMapContainer,
        TournamentNameAndIDMapContainer,
    },
    utils::{
        error_to_reply::error_to_reply,
        spin_lock::spin_mut,
        tourn_resolver::{admin_tourn_id_resolver, player_tourn_resolver, user_id_resolver},
    },
};

#[command("name")]
#[only_in(guild)]
#[usage("[tournament name]")]
#[description("Adjust your name in the tournament.")]
async fn name(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    // Resolve the tournament id
    let gamer_tag = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please include your gamer tag.")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match player_tourn_resolver(
        ctx,
        msg,
        tourn_name,
        all_tourns,
        ids.get_left_iter(&msg.guild_id.unwrap()).unwrap(),
    )
    .await
    {
        None => {
            return Ok(());
        }
        Some(id) => id,
    };
    let mut tourn = spin_mut(all_tourns, &tourn_id).await.unwrap();
    let plyr_id = match tourn.players.get_right(&msg.author.id) {
        Some(id) => PlayerIdentifier::Id(id.clone()),
        None => {
            msg.reply(&ctx.http, "You are not registered for that tournament.")
                .await?;
            return Ok(());
        }
    };
    if let Err(err) = tourn
        .tourn
        .apply_op(TournOp::SetGamerTag(plyr_id, gamer_tag))
    {
        error_to_reply(ctx, msg, err).await?;
    } else {
        msg.reply(&ctx.http, "Deck successfully added!").await?;
    }
    Ok(())
}
