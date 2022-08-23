use serenity::{
    async_trait,
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_lib::{
    operations::TournOp, player_registry::PlayerIdentifier, tournament::TournamentId,
    identifiers::AdminId,
};

use crate::{
    model::{
        confirmation::Confirmation,
        containers::{
            ConfirmationsContainer, GuildAndTournamentIDMapContainer, TournamentMapContainer,
            TournamentNameAndIDMapContainer,
        },
        consts::SQUIRE_ACCOUNT_ID,
    },
    utils::{
        error_to_reply::error_to_reply,
        spin_lock::spin_mut,
        tourn_resolver::{admin_tourn_id_resolver, user_id_resolver},
    },
};

#[command("cut")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("<top N>, [tournament name]")]
#[example("16")]
#[description("Drops all but the top N players.")]
async fn cut(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    // Resolve cut size
    let len = match args.single_quoted::<usize>() {
        Ok(n) => n,
        Err(_) => {
            msg.reply(&ctx.http, "Please include the number you wish to cut to.")
                .await?;
            return Ok(());
        }
    };
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
        Box::new(CutToTopConfirmation { tourn_id, len }),
    );
    msg.reply(
        &ctx.http,
        format!(
            "Are you sure you want to cut the tournament to the top {}? !yes or !no",
            len
        ),
    )
    .await?;
    Ok(())
}

struct CutToTopConfirmation {
    tourn_id: TournamentId,
    len: usize,
}

#[async_trait]
impl Confirmation for CutToTopConfirmation {
    async fn execute(&mut self, ctx: &Context, msg: &Message) -> CommandResult {
        let data = ctx.data.read().await;
        let all_tourns = data.get::<TournamentMapContainer>().unwrap();
        let mut tourn = spin_mut(all_tourns, &self.tourn_id).await.unwrap();
        if let Err(err) = tourn.tourn.apply_op(TournOp::Cut(*SQUIRE_ACCOUNT_ID, self.len)) {
            error_to_reply(ctx, msg, err).await?;
        } else {
            tourn.update_status = true;
            msg.reply(
                &ctx.http,
                format!("Tournament successfully cut to the top {}!", self.len),
            )
            .await?;
        }
        Ok(())
    }
}
