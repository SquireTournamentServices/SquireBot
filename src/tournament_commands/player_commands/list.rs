use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
    utils::MessageBuilder,
};

use crate::model::{
    containers::{
        GuildAndTournamentIDMapContainer, TournamentMapContainer, TournamentNameAndIDMapContainer,
    },
    guild_tournament::GuildTournament,
};

#[command("list")]
#[only_in(guild)]
#[description("Lists out all tournament in the server.")]
async fn list(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    /* Get references to needed data from context */
    let data = ctx.data.read().await;
    let name_and_id = data
        .get::<TournamentNameAndIDMapContainer>()
        .unwrap()
        .read()
        .await;
    let gld_tourns = data
        .get::<GuildAndTournamentIDMapContainer>()
        .unwrap()
        .read()
        .await;

    //Check if there are any active tournaments. If so list them, if not report that to the user
    match gld_tourns.get_left_iter(&msg.guild_id.unwrap()) {
        None => {
            msg.reply(
                &ctx.http,
                "There are no tournaments being held in this server.",
            )
            .await?;
        }
        Some(id_iter) => {
            let mut response = MessageBuilder::new();
            for tourn in id_iter {
                response
                    .push_bold_safe(name_and_id.get_left(&tourn).unwrap())
                    .push("\n");
            }
            msg.reply(&ctx.http, response.build()).await?;
        }
    };
    Ok(())
}
