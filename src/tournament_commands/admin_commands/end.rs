use serenity::{
    async_trait,
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_lib::{
    identifiers::AdminId, operations::TournOp, player_registry::PlayerIdentifier,
    tournament::TournamentId,
};

use crate::{
    model::{
        confirmation::Confirmation,
        consts::SQUIRE_ACCOUNT_ID,
        containers::{
            ConfirmationsContainer, GuildAndTournamentIDMapContainer, TournamentMapContainer,
            TournamentNameAndIDMapContainer,
        },
    },
    utils::{
        error_to_reply::error_to_reply,
        spin_lock::spin_mut,
        tourn_resolver::{admin_tourn_id_resolver, user_id_resolver},
    },
};

#[command("end")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("[tournament name]")]
#[example("end")]
#[description("Ends a tournament.")]
async fn end(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let confs = data.get::<ConfirmationsContainer>().unwrap();
    confs.insert(
        msg.author.id,
        Box::new(EndTournamentConfirmation { tourn_id }),
    );
    msg.reply(
        &ctx.http,
        "Are you sure you want to end the tournament? !yes or !no",
    )
    .await?;
    Ok(())
}

struct EndTournamentConfirmation {
    tourn_id: TournamentId,
}

#[async_trait]
impl Confirmation for EndTournamentConfirmation {
    async fn execute(&mut self, ctx: &Context, msg: &Message) -> CommandResult {
        let data = ctx.data.read().await;
        let all_tourns = data.get::<TournamentMapContainer>().unwrap().read().await;
        let mut tourn = spin_mut(&all_tourns, &self.tourn_id).await.unwrap();
        if let Err(err) = tourn.tourn.apply_op(TournOp::End(*SQUIRE_ACCOUNT_ID)) {
            error_to_reply(ctx, msg, err).await?;
        } else {
            tourn.update_status = true;
            msg.reply(&ctx.http, "Tournament successfully ended!")
                .await?;
        }
        Ok(())
    }
}
