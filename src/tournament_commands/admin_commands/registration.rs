use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
    CacheAndHttp,
};

use squire_lib::{operations::TournOp, player_registry::PlayerIdentifier};

use crate::{
    model::containers::{
        GuildAndTournamentIDMapContainer, TournamentMapContainer, TournamentNameAndIDMapContainer,
    },
    utils::{
        error_to_reply::error_to_reply,
        spin_lock::spin_mut,
        stringify::bool_from_string,
        tourn_resolver::{admin_tourn_id_resolver, user_id_resolver},
    },
};

#[command("registration")]
#[only_in(guild)]
#[aliases("reg")]
#[allowed_roles("Tournament Admin")]
#[usage("<open/closed>, [tournament name]")]
#[description("Changes the registeration status of the tournament.")]
async fn registration(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let raw_reg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, r#"Please specify "open" or "closed"."#)
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let reg_status = match raw_reg.as_str() {
        "open" | "Open" => true,
        "closed" | "Closed" => false,
        _ => {
            msg.reply(&ctx.http, r#"Please specify "open" or "closed"."#)
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
    let mut tourn = spin_mut(all_tourns, &tourn_id).await.unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateReg(reg_status)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Registration successfully updated.")
            .await?;
    }
    Ok(())
}
