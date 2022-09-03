use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
    CacheAndHttp,
};

use squire_lib::{
    operations::TournOp, player_registry::PlayerIdentifier, round_registry::RoundIdentifier,
};

use crate::{
    model::containers::{
        GuildAndTournamentIDMapContainer, TournamentMapContainer, TournamentNameAndIDMapContainer,
    },
    utils::{
        embeds::update_standings_message,
        error_to_reply::error_to_reply,
        spin_lock::spin_mut,
        stringify::bool_from_string,
        tourn_resolver::{admin_tourn_id_resolver, player_name_resolver, user_id_resolver},
    },
};

#[command("standings")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("[tournament name]")]
#[description("Creates an auto-updating standings message.")]
async fn standings(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = spin_mut(&all_tourns, &tourn_id).await.unwrap();
    let standings = tourn.tourn.get_standings();
    let standings_message = msg.reply(ctx, "Standings will appear soon...").await?;
    tourn.standings_message = Some(standings_message);
    Ok(())
}
