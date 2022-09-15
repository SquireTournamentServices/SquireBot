use serenity::{
    async_trait, framework::standard::CommandResult, model::channel::Message, prelude::Context,
};

use squire_lib::{error::TournamentError, identifiers::TournamentId, operations::TournOp};

use crate::{
    model::{
        consts::SQUIRE_ACCOUNT_ID,
        containers::{DeadTournamentMapContainer, TournamentMapContainer},
    },
    utils::{error_to_reply::error_to_content, spin_lock::spin_mut},
};

#[async_trait]
pub trait Confirmation
where
    Self: Send + Sync,
{
    async fn execute(&mut self, ctx: &Context, msg: &Message) -> CommandResult;
}

struct CutToTopConfirmation {
    tourn_id: TournamentId,
    len: usize,
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
            msg.reply(
                &ctx.http,
                format!("Tournament successfully cut to the top {}!", self.len),
            )
            .await?;
        }
        Ok(())
    }
}

struct EndTournamentConfirmation {
    tourn_id: TournamentId,
}

#[async_trait]
impl Confirmation for EndTournamentConfirmation {
    async fn execute(&mut self, ctx: &Context, msg: &Message) -> CommandResult {
        let data = ctx.data.read().await;
        let all_tourns = data.get::<TournamentMapContainer>().unwrap().write().await;
        let (_, tourn) = all_tourns
            .remove(&self.tourn_id)
            .ok_or_else(|| Box::new(TournamentError::PlayerLookup))?;
        if let Err(err) = tourn.end().await {
            msg.reply(&ctx.http, error_to_content(err)).await?;
        } else {
            let dead_tourns = data
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

struct CancelTournamentConfirmation {
    tourn_id: TournamentId,
}

#[async_trait]
impl Confirmation for CancelTournamentConfirmation {
    async fn execute(&mut self, ctx: &Context, msg: &Message) -> CommandResult {
        let data = ctx.data.read().await;
        let all_tourns = data.get::<TournamentMapContainer>().unwrap().write().await;
        let (_, tourn) = all_tourns
            .remove(&self.tourn_id)
            .ok_or_else(|| Box::new(TournamentError::PlayerLookup))?;
        if let Err(err) = tourn.cancel().await {
            msg.reply(&ctx.http, error_to_content(err)).await?;
        } else {
            let dead_tourns = data
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

struct PrunePlayersConfirmation {
    tourn_id: TournamentId,
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
        let all_tourns = data.get::<TournamentMapContainer>().unwrap().read().await;
        let mut tourn = spin_mut(&all_tourns, &self.tourn_id).await.unwrap();
        if let Err(err) = tourn
            .tourn
            .apply_op(TournOp::PruneDecks(*SQUIRE_ACCOUNT_ID))
        {
            msg.reply(&ctx.http, error_to_content(err)).await?;
        } else {
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

struct PairRoundConfirmation {
    tourn_id: TournamentId,
}

#[async_trait]
impl Confirmation for PairRoundConfirmation {
    async fn execute(&mut self, ctx: &Context, msg: &Message) -> CommandResult {
        let data = ctx.data.read().await;
        let all_tourns = data.get::<TournamentMapContainer>().unwrap().read().await;
        let mut tourn = spin_mut(&all_tourns, &self.tourn_id).await.unwrap();
        if let Err(err) = tourn.tourn.apply_op(TournOp::PairRound(*SQUIRE_ACCOUNT_ID)) {
            msg.reply(&ctx.http, error_to_content(err)).await?;
        } else {
            msg.reply(
                &ctx.http,
                "Players have now been paired for the next round!!",
            )
            .await?;
        }
        Ok(())
    }
}
