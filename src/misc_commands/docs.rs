use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;
use serenity::utils::Color;

static ALL_DOCS: &str = "";
static PLAYER_DOC: &str = "";
static TO_DOC: &str = "";
static FAQ_DOC: &str = "";
static ABOUT_DOC: &str = "";

#[command("docs")]
#[description("Provides locations where you can read more about how SquireBot works.")]
async fn docs(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    let mut message = msg.reply(&ctx.http, "\u{200b}").await?;
    message
        .edit(&ctx.http, |m| {
            m.embed(|e| {
                e.title("Docs Pages")
                    .color(Color::from_rgb(0, 117, 202))
                    .field(
                        "All Docs:",
                        format!("You can find all of our user docs [here]({ALL_DOCS}). This includes docs for players, TOs, an FAQ, and overview of how SquireBot 'thinks' about tournaments."),
                        true,
                    )
                    .field(
                        "Player Docs:",
                        format!("If you are a player and want to see what you need to do to play in a tournament ran with SquireBot, go [here]({PLAYER_DOC})."),
                        true,
                    )
                    .field(
                        "TO Docs:",
                        format!("If you are a judge/TO that is using SquireBot to run a tournament, you probably want to start [here]({ABOUT_DOC}). This will go over how SquireBot 'thinks' about tournaments, so you can be on the same wavelength. There is also a 'get started' guide [here]({TO_DOC}). Lastly, there is an FAQ/troubleshooting doc [here]({FAQ_DOC})."),
                        true,
                    )
            })
        })
        .await?;
    Ok(())
}
