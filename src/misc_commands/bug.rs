use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;
use serenity::utils::Color;

static USER_BUG_URL: &str = "https://github.com/MonarchDevelopment/SquireBot/issues/new?assignees=&labels=bug%2C+review&template=bug_report.md&title=%5BBug%5D%3A+";
static DEV_SERVER_BUG_URL: &str = "https://discord.gg/pTjRkBv6tV";

#[command("bug")]
#[description("Provides locations where you can submit bug reports.")]
async fn bug(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    let mut message = msg.reply(&ctx.http, "\u{200b}").await?;
    message
        .edit(&ctx.http, |m| {
            m.embed(|e| {
                e.title("Bug Report")
                    .color(Color::from_rgb(215, 58, 74))
                    .field(
                        "GitHub:",
                        format!("You can submit your bug report directly on GitHub. Just go [here]({USER_BUG_URL})."),
                        true,
                    )
                    .field(
                        "Discord:",
                        format!("Alternatively, you can talk to the devs. Just go [here]({DEV_SERVER_BUG_URL})."),
                        true,
                    )
            })
        })
        .await?;
    Ok(())
}
