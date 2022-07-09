use std::fmt::Write;

use serenity::{
    async_trait,
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_core::{
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
        error_to_reply::error_to_reply,
        spin_lock::{spin, spin_mut},
        tourn_resolver::{admin_tourn_id_resolver, user_id_resolver},
    },
};

#[command("prune")]
#[only_in(guild)]
#[sub_commands(players, decks)]
#[allowed_roles("Tournament Admin")]
#[usage("<option>")]
#[description(
    "Removes players that aren't fully registered and decks from players that have them in excess."
)]
async fn prune(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    msg.reply(&ctx.http, "Please specify a subcommand.").await?;
    Ok(())
}

#[command("players")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("[tournament name]")]
#[description("Removes players that aren't fully registered.")]
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
    let tourn = spin(all_tourns, &tourn_id).await.unwrap();
    let mut req_text = String::new();
    let mut has_req = false;
    if tourn.tourn.require_check_in {
        let _ = write!(req_text, "checked in");
        has_req = true;
    }
    if tourn.tourn.require_deck_reg {
        if !req_text.is_empty() {
            let _ = write!(req_text, " and have not ");
        }
        let _ = write!(
            req_text,
            "registered at least {} deck{}",
            tourn.tourn.min_deck_count,
            if tourn.tourn.min_deck_count == 1 {
                ""
            } else {
                "s"
            }
        );
        has_req = true;
    }
    if !has_req {
        msg.reply(
            &ctx.http,
            "This tournament doesn't require additional registeration steps. Enable the require deck registeration and/or require check in settings in order to prune players.",
        )
        .await?;
        return Ok(());
    }
    let confs = data.get::<ConfirmationsContainer>().unwrap();
    confs.insert(msg.author.id, Box::new(PruneDecksConfirmation { tourn_id }));
    msg.reply(
        &ctx.http,
        format!(
            "You are about to drop all players that have not {}. Are you sure you want to do this? !yes or !no.",
            req_text,
        ),
    )
    .await?;
    Ok(())
}

#[command("decks")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("[tournament name]")]
#[description("Removes decks from players that have them in excess.")]
async fn decks(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let tourn = spin(all_tourns, &tourn_id).await.unwrap();
    if !tourn.tourn.require_deck_reg {
        msg.reply(
            &ctx.http,
            "This tournament doesn't require players to register decks. Enable this setting in order to prune decks.",
        )
        .await?;
        return Ok(());
    }
    let confs = data.get::<ConfirmationsContainer>().unwrap();
    confs.insert(msg.author.id, Box::new(PruneDecksConfirmation { tourn_id }));
    msg.reply(
        &ctx.http,
        format!(
            "You are about to remove excess decks that players have registered. After this, every player will have a max of {} deck{}. Are you sure you want to do this? !yes or !no. Note: Older decks are removed first.",
            tourn.tourn.max_deck_count,
            if tourn.tourn.max_deck_count == 1 { "" } else { "s"},
        ),
    )
    .await?;
    Ok(())
}

struct PrunePlayersConfirmation {
    tourn_id: TournamentId,
}

#[async_trait]
impl Confirmation for PrunePlayersConfirmation {
    async fn execute(&mut self, ctx: &Context, msg: &Message) -> CommandResult {
        let data = ctx.data.read().await;
        let all_tourns = data.get::<TournamentMapContainer>().unwrap();
        let mut tourn = spin_mut(all_tourns, &self.tourn_id).await.unwrap();
        if let Err(err) = tourn.tourn.apply_op(TournOp::PrunePlayers()) {
            error_to_reply(ctx, msg, err).await?;
        } else {
            tourn.update_status = true;
            msg.reply(
                &ctx.http,
                "Players that were to completely registered have been successfully dropped!",
            )
            .await?;
        }
        Ok(())
    }
}

struct PruneDecksConfirmation {
    tourn_id: TournamentId,
}

#[async_trait]
impl Confirmation for PruneDecksConfirmation {
    async fn execute(&mut self, ctx: &Context, msg: &Message) -> CommandResult {
        let data = ctx.data.read().await;
        let all_tourns = data.get::<TournamentMapContainer>().unwrap();
        let mut tourn = spin_mut(all_tourns, &self.tourn_id).await.unwrap();
        if let Err(err) = tourn.tourn.apply_op(TournOp::PruneDecks()) {
            error_to_reply(ctx, msg, err).await?;
        } else {
            tourn.update_status = true;
            msg.reply(
                &ctx.http,
                format!(
                    "Players that registered too many decks now have at most {}!",
                    tourn.tourn.max_deck_count
                ),
            )
            .await?;
        }
        Ok(())
    }
}
