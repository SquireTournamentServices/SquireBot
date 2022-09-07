
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
        let all_tourns = data.get::<TournamentMapContainer>().unwrap().read().await;
        let mut tourn = spin_mut(&all_tourns, &self.tourn_id).await.unwrap();
        if let Err(err) = tourn
            .tourn
            .apply_op(TournOp::PruneDecks(*SQUIRE_ACCOUNT_ID))
        {
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
