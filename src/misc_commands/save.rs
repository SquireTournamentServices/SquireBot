use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use crate::model::containers::GuildTournRegistryMapContainer;

use std::{fs::File, io::Write};

#[command("save")]
#[owners_only]
#[help_available(false)]
#[description("Force saves all data.")]
async fn save(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let tourn_regs = data
        .get::<GuildTournRegistryMapContainer>()
        .unwrap()
        .write()
        .await;
    let content = match serde_json::to_string(&*tourn_regs) {
        Ok(data) => match File::create("tournaments.json") {
            Ok(mut file) => match write!(file, "{data}") {
                Ok(_) => "Tournament data saved.",
                Err(_) => "Failed to write tournament data to file. **DATA NOT SAVED**.",
            },
            Err(_) => "Failed to create tournament file. **DATA NOT SAVED**.",
        },
        Err(_) => "Failed to serialize tournament. **DATA NOT SAVED**.",
    };
    msg.reply(&ctx.http, content).await?;
    Ok(())
}
