use chrono::Utc;
use serenity::{
    async_trait, framework::standard::CommandResult, model::channel::Message, prelude::Context,
};

use squire_lib::{
    identifiers::TournamentId,
    operations::{AdminOp::*, OpData, TournOp},
};

use crate::{
    logging::LogAction,
    match_manager::{MatchUpdate, MatchUpdateMessage},
    model::{
        consts::SQUIRE_ACCOUNT_ID,
        containers::{
            DeadTournamentMapContainer, LogActionSenderContainer, MatchUpdateSenderContainer,
        },
    },
    utils::{default_response::error_to_content, spin_lock::spin_mut},
};

use super::containers::GuildTournRegistryMapContainer;

#[async_trait]
pub trait Confirmation
where
    Self: Send + Sync,
{
    async fn execute(&mut self, ctx: &Context, msg: &Message) -> CommandResult;
}

pub struct CutToTopConfirmation {
    pub tourn_id: TournamentId,
    pub len: usize,
}

#[async_trait]
impl Confirmation for CutToTopConfirmation {
    async fn execute(&mut self, ctx: &Context, msg: &Message) -> CommandResult {
        let data = ctx.data.read().await;
        let logger = data.get::<LogActionSenderContainer>().unwrap();
        let _ = logger.send((msg.id, LogAction::Info("Cutting to top N")));
        let tourn_regs = data
            .get::<GuildTournRegistryMapContainer>()
            .unwrap()
            .read()
            .await;
        let g_id = msg.guild_id.unwrap();
        let mut reg = spin_mut(&tourn_regs, &g_id).await.unwrap();
        let tourn = reg.tourns.get_mut(&self.tourn_id).unwrap();
        if let Err(err) = tourn
            .tourn
            .apply_op(Utc::now(), TournOp::AdminOp(*SQUIRE_ACCOUNT_ID, Cut(self.len)))
        {
            msg.reply(&ctx.http, error_to_content(err)).await?;
        } else {
            tourn.update_status(ctx).await;
            tourn.update_standings(ctx).await;
            msg.reply(
                &ctx.http,
                format!("Tournament successfully cut to the top {}!", self.len),
            )
            .await?;
        }
        Ok(())
    }
}

pub struct EndTournamentConfirmation {
    pub tourn_id: TournamentId,
}

#[async_trait]
impl Confirmation for EndTournamentConfirmation {
    async fn execute(&mut self, ctx: &Context, msg: &Message) -> CommandResult {
        let data = ctx.data.read().await;
        let logger = data.get::<LogActionSenderContainer>().unwrap();
        let _ = logger.send((msg.id, LogAction::Info("Ending tournament")));
        let tourn_regs = data
            .get::<GuildTournRegistryMapContainer>()
            .unwrap()
            .read()
            .await;
        let g_id = msg.guild_id.unwrap();
        let _ = logger.send((
            msg.id,
            LogAction::CouldPanic("failed to find tournament registry"),
        ));
        let mut reg = spin_mut(&tourn_regs, &g_id).await.unwrap();
        let _ = logger.send((
            msg.id,
            LogAction::CouldPanic("failed to find tournament in registry"),
        ));
        let mut tourn = reg.remove_tourn(&self.tourn_id).await.unwrap();
        if let Err(err) = tourn.end(ctx).await {
            msg.reply(&ctx.http, error_to_content(err)).await?;
        } else {
            tourn.update_status(ctx).await;
            tourn.update_standings(ctx).await;
            let mut dead_tourns = data
                .get::<DeadTournamentMapContainer>()
                .unwrap()
                .write()
                .await;
            dead_tourns.insert(self.tourn_id, tourn);
            msg.reply(&ctx.http, "Tournament successfully ended!")
                .await?;
        }
        Ok(())
    }
}

pub struct CancelTournamentConfirmation {
    pub tourn_id: TournamentId,
}

#[async_trait]
impl Confirmation for CancelTournamentConfirmation {
    async fn execute(&mut self, ctx: &Context, msg: &Message) -> CommandResult {
        let data = ctx.data.read().await;
        let logger = data.get::<LogActionSenderContainer>().unwrap();
        let _ = logger.send((msg.id, LogAction::Info("Cancelling tournament")));
        let tourn_regs = data
            .get::<GuildTournRegistryMapContainer>()
            .unwrap()
            .read()
            .await;
        let g_id = msg.guild_id.unwrap();
        let _ = logger.send((
            msg.id,
            LogAction::CouldPanic("failed to find tournament registry"),
        ));
        let mut reg = spin_mut(&tourn_regs, &g_id).await.unwrap();
        let _ = logger.send((
            msg.id,
            LogAction::CouldPanic("failed to find tournament in registry"),
        ));
        let mut tourn = reg.remove_tourn(&self.tourn_id).await.unwrap();
        if let Err(err) = tourn.cancel(ctx).await {
            msg.reply(&ctx.http, error_to_content(err)).await?;
        } else {
            tourn.update_status(ctx).await;
            tourn.update_standings(ctx).await;
            reg.past_tourns.remove(&self.tourn_id);
            msg.reply(&ctx.http, "Tournament successfully cancelled!")
                .await?;
        }
        Ok(())
    }
}

pub struct PrunePlayersConfirmation {
    pub tourn_id: TournamentId,
}

#[async_trait]
impl Confirmation for PrunePlayersConfirmation {
    async fn execute(&mut self, ctx: &Context, msg: &Message) -> CommandResult {
        let data = ctx.data.read().await;
        let logger = data.get::<LogActionSenderContainer>().unwrap();
        let _ = logger.send((msg.id, LogAction::Info("Pruning players")));
        let tourn_regs = data
            .get::<GuildTournRegistryMapContainer>()
            .unwrap()
            .read()
            .await;
        let g_id = msg.guild_id.unwrap();
        let mut reg = spin_mut(&tourn_regs, &g_id).await.unwrap();
        let tourn = reg.tourns.get_mut(&self.tourn_id).unwrap();
        if let Err(err) = tourn
            .tourn
            .apply_op(Utc::now(), TournOp::AdminOp(*SQUIRE_ACCOUNT_ID, PrunePlayers))
        {
            msg.reply(&ctx.http, error_to_content(err)).await?;
        } else {
            tourn.update_status(ctx).await;
            tourn.update_standings(ctx).await;
            msg.reply(
                &ctx.http,
                "Players that were to completely registered have been successfully dropped!",
            )
            .await?;
        }
        Ok(())
    }
}

pub struct PruneDecksConfirmation {
    pub tourn_id: TournamentId,
}

#[async_trait]
impl Confirmation for PruneDecksConfirmation {
    async fn execute(&mut self, ctx: &Context, msg: &Message) -> CommandResult {
        let data = ctx.data.read().await;
        let logger = data.get::<LogActionSenderContainer>().unwrap();
        let _ = logger.send((msg.id, LogAction::Info("Pruning decks")));
        let tourn_regs = data
            .get::<GuildTournRegistryMapContainer>()
            .unwrap()
            .read()
            .await;
        let g_id = msg.guild_id.unwrap();
        let mut reg = spin_mut(&tourn_regs, &g_id).await.unwrap();
        let tourn = reg.tourns.get_mut(&self.tourn_id).unwrap();
        if let Err(err) = tourn
            .tourn
            .apply_op(Utc::now(), TournOp::AdminOp(*SQUIRE_ACCOUNT_ID, PruneDecks))
        {
            msg.reply(&ctx.http, error_to_content(err)).await?;
        } else {
            tourn.update_status(ctx).await;
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

pub struct PairRoundConfirmation {
    pub tourn_id: TournamentId,
}

#[async_trait]
impl Confirmation for PairRoundConfirmation {
    async fn execute(&mut self, ctx: &Context, msg: &Message) -> CommandResult {
        let data = ctx.data.read().await;
        let logger = data.get::<LogActionSenderContainer>().unwrap();
        let _ = logger.send((msg.id, LogAction::Info("Pairing next round")));
        let tourn_regs = data
            .get::<GuildTournRegistryMapContainer>()
            .unwrap()
            .read()
            .await;
        let g_id = msg.guild_id.unwrap();
        let mut reg = spin_mut(&tourn_regs, &g_id).await.unwrap();
        let tourn = reg.tourns.get_mut(&self.tourn_id).unwrap();
        match tourn
            .tourn
            .apply_op(Utc::now(), TournOp::AdminOp(*SQUIRE_ACCOUNT_ID, PairRound))
        {
            Err(err) => {
                msg.reply(&ctx.http, error_to_content(err)).await?;
            }
            Ok(OpData::Pair(rnds)) => {
                let sender = data.get::<MatchUpdateSenderContainer>().unwrap();
                for id in rnds {
                    let rnd = tourn.tourn.get_round(&(id.into())).unwrap().clone();
                    tourn
                        .create_round_data(ctx, &msg.guild(ctx).unwrap(), &rnd.id, rnd.match_number)
                        .await;
                    if let Some(tr) = tourn.get_tracking_round(&rnd.id) {
                        let message = MatchUpdateMessage {
                            id: rnd.id,
                            update: MatchUpdate::NewMatch(tr),
                        };
                        let _ = sender.send(message);
                    }
                }
                msg.reply(
                    &ctx.http,
                    "Players have now been paired for the next round!!",
                )
                .await?;
            }
            Ok(OpData::Nothing) => {
                msg.reply(
                    &ctx.http,
                    "Pairings could not be created. Make sure that all the matches are certified.",
                )
                .await?;
            }
            _ => {
                let _ = logger.send((
                    msg.id,
                    LogAction::CouldPanic("Reached unreachable branch!!"),
                ));
                unreachable!("Pairing a new round returns and `Err` or `Ok(OpData::Pair)`)");
            }
        }
        Ok(())
    }
}
