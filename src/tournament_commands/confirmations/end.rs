
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
