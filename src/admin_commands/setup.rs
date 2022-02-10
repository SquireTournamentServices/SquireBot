use crate::model::guild_settings::{
    GuildSettings, GuildSettingsContainer, DEFAULT_JUDGE_ROLE_NAME, DEFAULT_MATCHES_CATEGORY_NAME,
    DEFAULT_PAIRINGS_CHANNEL_NAME, DEFAULT_TOURN_ADMIN_ROLE_NAME,
};
use crate::utils::is_configured;

use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command("setup")]
#[sub_commands(check, test, defaults)]
#[only_in(guild)]
#[required_permissions("ADMINISTRATOR")]
#[description("Sets up the server to be able to run tournaments.")]
async fn setup(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let all_settings = data.get::<GuildSettingsContainer>().unwrap();
    let guild: Guild = msg.guild(&ctx.cache).unwrap();
    // Gets a copy of the setting. We don't want to a reference to the copy since creating what
    // needs to be created will trigger the hooks and update the shared settings object.
    let settings: GuildSettings = match all_settings.get_mut(&guild.id) {
        Some(s) => s.clone(),
        None => {
            // This case should never happen... but just in case
            all_settings.insert(guild.id.clone(), GuildSettings::from_existing(&guild));
            all_settings.get_mut(&guild.id).unwrap().clone()
        }
    };
    drop(all_settings);

    match settings.judge_role {
        Some(_) => {}
        None => {
            let _ = guild
                .create_role(&ctx.http, |r| r.name(DEFAULT_JUDGE_ROLE_NAME))
                .await?;
        }
    };
    match settings.tourn_admin_role {
        Some(_) => {}
        None => {
            let _ = guild
                .create_role(&ctx.http, |r| r.name(DEFAULT_TOURN_ADMIN_ROLE_NAME))
                .await?;
        }
    };
    match settings.pairings_channel {
        Some(_) => {}
        None => {
            let _ = guild
                .create_channel(&ctx.http, |r| {
                    r.name(DEFAULT_PAIRINGS_CHANNEL_NAME)
                        .kind(ChannelType::Text)
                })
                .await?;
        }
    };
    match settings.matches_category {
        Some(_) => {}
        None => {
            let _ = guild
                .create_channel(&ctx.http, |r| {
                    r.name(DEFAULT_MATCHES_CATEGORY_NAME)
                        .kind(ChannelType::Category)
                })
                .await?;
        }
    };

    msg.reply(
        &ctx.http,
        "The server should now be setup to run tournament. To test this, run `!setup test`.",
    )
    .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[required_permissions("ADMINISTRATOR")]
#[description("Prints out the current tournament-related settings.")]
async fn check(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[required_permissions("ADMINISTRATOR")]
#[description("Tests the setup of the server.")]
async fn test(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let all_settings = data.get::<GuildSettingsContainer>().unwrap();
    // Gets a copy of the setting. We don't want to a reference to the copy since creating what
    // needs to be created will trigger the hooks and update the shared settings object.
    let guild: Guild = msg.guild(&ctx.cache).unwrap();
    let settings: GuildSettings = match all_settings.get_mut(&guild.id) {
        Some(s) => s.clone(),
        None => {
            // This case should never happen... but just in case
            all_settings.insert(guild.id.clone(), GuildSettings::from_existing(&guild));
            all_settings.get_mut(&guild.id).unwrap().clone()
        }
    };
    drop(all_settings);
    let tests = String::from("Judge Role Exists:\nAdmin Role Exists:\nPairings Channel Exists:\nSend Pairings:\nEdit Pairings:\nSend Embed:\nEdit Embed:\nMatches Category Exists:\nCreate VC:\nDelete VC:\nCreate TC:\nDelete TC:");
    let mut test_results = String::new();
    match settings.judge_role {
        None => {
            test_results += "Failed - No judge role found.\n";
        }
        Some(_) => {
            test_results += "Passed\n";
        }
    }
    match settings.tourn_admin_role {
        None => {
            test_results += "Failed - No tournament admin role found.\n";
        }
        Some(_) => {
            test_results += "Passed\n";
        }
    }
    match settings.pairings_channel {
        None => {
            test_results += &"Failed - No pairings channel found.\n".repeat(5);
        }
        Some(id) => {
            test_results += "Passed\n";
            if let Channel::Guild(pairings_channel) = guild.channels.get(&id).unwrap() {
                match pairings_channel
                    .send_message(&ctx.http, |m| m.content("Testing..."))
                    .await
                {
                    Err(_) => {
                        test_results += &"Failed - Couldn't send message.\n".repeat(4);
                    }
                    Ok(m) => {
                        test_results += &"Passed\n";
                        match pairings_channel
                            .edit_message(&ctx.http, m.id, |m| m.content("Edited Test"))
                            .await
                        {
                            Ok(_) => {
                                test_results += "Passed\n";
                            }
                            Err(_) => {
                                test_results += "Failed - Couldn't delete message.\n";
                            }
                        }
                    }
                }
                match pairings_channel
                    .send_message(&ctx.http, |m| m.embed(|e| e.title("Test Embed")))
                    .await
                {
                    Err(_) => {
                        test_results += &"Failed - Couldn't send embed.\n".repeat(2);
                    }
                    Ok(m) => {
                        test_results += &"Passed\n";
                        match pairings_channel
                            .edit_message(&ctx.http, m.id, |m| {
                                m.embed(|e| e.title("Edited Test Embed"))
                            })
                            .await
                        {
                            Ok(_) => {
                                test_results += "Passed\n";
                            }
                            Err(_) => {
                                test_results += "Failed - Couldn't delete embed.\n";
                            }
                        }
                    }
                }
            } else {
                test_results += &"Failed - No pairings channel isn't text channel.\n".repeat(4);
            }
        }
    }
    if settings.make_tc || settings.make_vc {
        match settings.matches_category {
            None => {
                test_results += &"Failed - No matches category found.\n".repeat(5);
            }
            Some(id) => {
                if let Channel::Category(matches_category) = guild.channels.get(&id).unwrap() {
                    test_results += "Passed\n";
                    if settings.make_vc {
                        match guild
                            .create_channel(&ctx.http, |c| {
                                c.name("Test VC").kind(ChannelType::Voice).category(id)
                            })
                            .await
                        {
                            Ok(c) => {
                                test_results += &"Passed\n";
                                match c.delete(&ctx.http).await {
                                    Ok(_) => {
                                        test_results += "Passed\n";
                                    }
                                    Err(_) => {
                                        test_results += "Failed - Couldn't delete VC.\n";
                                    }
                                }
                            }
                            Err(_) => {
                                test_results += &"Failed - VC not made.\n".repeat(2);
                            }
                        }
                    } else {
                        test_results += &"Omitted - Not making VCs.\n".repeat(2);
                    }
                    if settings.make_tc {
                        match guild
                            .create_channel(&ctx.http, |c| {
                                c.name("Test TC").kind(ChannelType::Text).category(id)
                            })
                            .await
                        {
                            Ok(c) => {
                                test_results += &"Passed\n";
                                match c.delete(&ctx.http).await {
                                    Ok(_) => {
                                        test_results += "Passed\n";
                                    }
                                    Err(_) => {
                                        test_results += "Failed - Couldn't delete TC.\n";
                                    }
                                }
                            }
                            Err(_) => {
                                test_results += &"Failed - TC not made.\n".repeat(2);
                            }
                        }
                    } else {
                        test_results += &"Omitted - Not making TCs.\n".repeat(2);
                    }
                }
            }
        }
    } else {
        test_results += &"Omitted - Not making TCs nor VCs.\n".repeat(5);
    }
    if let Channel::Guild(c) = msg.channel(&ctx.http).await? {
        c.send_message(&ctx.http, |m| {
            m.embed(|e| {
                e.title("Test Results").fields(vec![
                    ("Tests", tests, true),
                    ("Results", test_results, true),
                ])
            })
        })
        .await?;
    } else {
        msg.reply(&ctx.http, "How did you send this??").await?;
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[required_permissions("ADMINISTRATOR")]
#[description("Changes the default settings for new tournament in the server.")]
async fn defaults(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}
