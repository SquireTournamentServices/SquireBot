use serenity::framework::standard::CommandResult;

pub trait Confirmation
where
    Self: Send + Sync,
{
    fn execute(&mut self) -> String;
}
