use serenity::{
    async_trait,
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_lib::{
    operations::TournOp, player_registry::PlayerIdentifier, tournament::TournamentId,
};

use crate::{
    model::{
        confirmation::Confirmation,
        containers::{
            ConfirmationsContainer, GuildAndTournamentIDMapContainer, TournamentMapContainer,
            TournamentNameAndIDMapContainer,
        },
    },
    utils::{
        embeds::embed_fields,
        error_to_reply::error_to_reply,
        spin_lock::spin,
        tourn_resolver::{admin_tourn_id_resolver, player_name_resolver, user_id_resolver},
    },
};

#[command("players")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("[tournament name]")]
#[description("Prints out a list of all players.")]
async fn players(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let tourn = spin(all_tourns, &tourn_id).await.unwrap();
    let name_iter = tourn
        .tourn
        .player_reg
        .players
        .iter()
        .map(|(id, _)| player_name_resolver(id.clone(), &tourn.players, &tourn.tourn));
    let len = name_iter.len();
    let fields = embed_fields(name_iter)
        .into_iter()
        .map(|f| ("Players", f, false));
    if let Channel::Guild(c) = msg.channel(&ctx.http).await? {
        c.send_message(&ctx.http, |m| {
            m.embed(|e| e.title(format!("Players: ({len})")).fields(fields))
        })
        .await?;
    }
    Ok(())
}
