use serenity::{framework::standard::CommandResult, model::prelude::Message, prelude::Context};

pub async fn subcommand_default(ctx: &Context, msg: &Message, cmd: &str) -> CommandResult {
    msg.reply(
        &ctx.http,
        format!("Please specify a subcommand. If you're unsure, use `!sb-help {cmd}`."),
    )
    .await?;
    Ok(())
}
