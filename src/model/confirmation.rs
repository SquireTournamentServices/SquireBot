use serenity::{
    async_trait, framework::standard::CommandResult, model::channel::Message, prelude::Context,
};

use squire_lib::{
    error::TournamentError,
    identifiers::TournamentId,
    operations::{OpData, TournOp},
};

use crate::{
    model::{
        consts::SQUIRE_ACCOUNT_ID,
        containers::{DeadTournamentMapContainer, TournamentMapContainer},
    },
    utils::{default_response::error_to_content, spin_lock::spin_mut}, match_manager::{MatchUpdate, MatchUpdateMessage},
};

use super::containers::MatchUpdateSenderContainer;

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
        let all_tourns = data.get::<TournamentMapContainer>().unwrap().read().await;
        let mut tourn = spin_mut(&all_tourns, &self.tourn_id).await.unwrap();
        if let Err(err) = tourn
            .tourn
            .apply_op(TournOp::Cut(*SQUIRE_ACCOUNT_ID, self.len))
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
        let all_tourns = data.get::<TournamentMapContainer>().unwrap().write().await;
        let (_, mut tourn) = all_tourns
            .remove(&self.tourn_id)
            .ok_or_else(|| Box::new(TournamentError::PlayerLookup))?;
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
        let all_tourns = data.get::<TournamentMapContainer>().unwrap().write().await;
        let (_, mut tourn) = all_tourns
            .remove(&self.tourn_id)
            .ok_or_else(|| Box::new(TournamentError::PlayerLookup))?;
        if let Err(err) = tourn.cancel(ctx).await {
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
        let all_tourns = data.get::<TournamentMapContainer>().unwrap().read().await;
        let mut tourn = spin_mut(&all_tourns, &self.tourn_id).await.unwrap();
        if let Err(err) = tourn
            .tourn
            .apply_op(TournOp::PrunePlayers(*SQUIRE_ACCOUNT_ID))
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
        let all_tourns = data.get::<TournamentMapContainer>().unwrap().read().await;
        let mut tourn = spin_mut(&all_tourns, &self.tourn_id).await.unwrap();
        if let Err(err) = tourn
            .tourn
            .apply_op(TournOp::PruneDecks(*SQUIRE_ACCOUNT_ID))
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
        let all_tourns = data.get::<TournamentMapContainer>().unwrap().read().await;
        let mut tourn = spin_mut(&all_tourns, &self.tourn_id).await.unwrap();
        match tourn.tourn.apply_op(TournOp::PairRound(*SQUIRE_ACCOUNT_ID)) {
            Err(err) => {
                msg.reply(&ctx.http, error_to_content(err)).await?;
            }
            Ok(OpData::Pair(rnds)) => {
                let sender = data.get::<MatchUpdateSenderContainer>().unwrap();
                for ident in rnds {
                    let rnd = tourn.tourn.get_round(&ident).unwrap();
                    tourn.create_round_data(ctx, &msg.guild(ctx).unwrap(), &rnd.id, rnd.match_number).await;
                    if let Some(tr) = tourn.get_tracking_round(&rnd.id) {
                        let message = MatchUpdateMessage {
                            id: rnd.id,
                            update: MatchUpdate::NewMatch(tr),
                        };
                        sender.send(message);
                    }
                }
                msg.reply(
                    &ctx.http,
                    "Players have now been paired for the next round!!",
                )
                .await?;
                todo!()
            }
            _ => {
                unreachable!("Pairing a new round returns and `Err` or `Ok(OpData::Pair)`)");
            }
        }
        Ok(())
    }
}
