use serenity::{
    async_trait, framework::standard::CommandResult, model::channel::Message, prelude::Context,
};

#[async_trait]
pub trait Confirmation
where
    Self: Send + Sync,
{
    async fn execute(&mut self, ctx: &Context, msg: &Message) -> CommandResult;
}
