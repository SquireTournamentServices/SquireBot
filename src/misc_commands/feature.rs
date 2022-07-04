use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;
use serenity::utils::Color;

static USER_FEATURE_URL: &str = "https://github.com/MonarchDevelopment/SquireBot/issues/new?assignees=&labels=feature%2C+review&template=feature_request.md&title=%5BBug%5D%3A+";
static DEV_SERVER_FEATURE_URL: &str = "https://discord.gg/P5msA3Cu8Y";

#[command("feature")]
#[aliases("feat")]
#[usage("!feature")]
#[example("`!feature` or `!feat`")]
#[description("Provides locations where you can submit request features.")]
async fn feature(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    let mut message = msg.reply(&ctx.http, "\u{200b}").await?;
    message
        .edit(&ctx.http, |m| {
            m.embed(|e| {
                e.title("Feature Request")
                    .color(Color::from_rgb(83, 25, 231))
                    .field(
                        "GitHub:",
                        format!("You can submit your feature request directly on GitHub. Just go [here]({USER_FEATURE_URL})."),
                        true,
                    )
                    .field(
                        "Discord:",
                        format!("Alternatively, you can talk to the devs. Just go [here]({DEV_SERVER_FEATURE_URL})."),
                        true,
                    )
            })
        })
        .await?;
    Ok(())
}
