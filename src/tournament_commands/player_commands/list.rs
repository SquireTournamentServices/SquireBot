use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("list")]
#[only_in(guild)]
#[description("Lists out all tournament in the server.")]
async fn list(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    /* Get references to needed data from context */
    let data = ctx.data.read().await;
    let name_and_id = data.get::<TournamentNameAndIDMapContainer>().unwrap();
    let gld_tourns = data.get::<GuildAndTournamentIDMapContainer>().unwrap();

    //Check if there are any active tournaments. If so list them, if not report that to the user
    let id_iter = gld_tourns.get_left_iter(&msg.guild_id.unwrap()).unwrap();
    let tourn_id = match id_iter.len() {
        0 => {
            msg.reply(
                &ctx.http,
                "There are no tournaments being held in this server.",
            )
            .await?;
            return Ok(());
        },
        _ => {
            let response = MessageBuilder::new();
            for tourn in id_iter {
                response
                .push_bold_safe(&tourn)
                .push("\n");
            }
            response.build();

            msg.reply(
                &ctx.http,
                response
            )
            .await?;
            return Ok(());
        }
    };
}
