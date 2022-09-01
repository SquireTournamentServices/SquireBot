use crate::model::consts::*;
use crate::model::{containers::GuildSettingsMapContainer, guild_settings::GuildSettings};
use crate::utils::spin_lock::{spin, spin_mut};
//use crate::utils::is_configured;

use super::defaults_commands::*;

use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

// TODO: Find a work around for this
//#[required_permissions("ADMINISTRATOR")]
#[command("setup")]
#[sub_commands(view, test, defaults)]
#[usage("<view/test/defaults>")]
#[only_in(guild)]
#[description("Sets up the server to be able to run tournaments.")]
async fn setup(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let all_settings = data.get::<GuildSettingsMapContainer>().unwrap().read().await;
    let guild: Guild = msg.guild(&ctx.cache).unwrap();
    // Gets a copy of the setting. We don't want to a reference to the copy since creating what
    // needs to be created will trigger the hooks and update the shared settings object.
    let settings: GuildSettings = match spin(&all_settings, &guild.id).await {
        Some(s) => s.clone(),
        None => {
            // This case should never happen... but just in case
            all_settings.insert(guild.id, GuildSettings::from_existing(&guild));
            spin_mut(&all_settings, &guild.id).await.unwrap().clone()
        }
    };

    if settings.judge_role.is_none() {
        let _ = guild
            .create_role(&ctx.http, |r| r.name(DEFAULT_JUDGE_ROLE_NAME))
            .await?;
    };
    if settings.tourn_admin_role.is_none() {
        guild
            .create_role(&ctx.http, |r| r.name(DEFAULT_TOURN_ADMIN_ROLE_NAME))
            .await?;
    };
    if settings.pairings_channel.is_none() {
        guild
            .create_channel(&ctx.http, |r| {
                r.name(DEFAULT_PAIRINGS_CHANNEL_NAME)
                    .kind(ChannelType::Text)
            })
            .await?;
    };
    if settings.matches_category.is_none() {
        guild
            .create_channel(&ctx.http, |r| {
                r.name(DEFAULT_MATCHES_CATEGORY_NAME)
                    .kind(ChannelType::Category)
            })
            .await?;
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
#[allowed_roles("Tournament Admin")]
#[description("Prints out the current tournament-related settings.")]
async fn view(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let all_settings = data.get::<GuildSettingsMapContainer>().unwrap().read().await;
    // Gets a copy of the setting. We don't want to a reference to the copy since creating what
    // needs to be created will trigger the hooks and update the shared settings object.
    let guild: Guild = msg.guild(&ctx.cache).unwrap();
    let settings: GuildSettings = match spin_mut(&all_settings, &guild.id).await {
        Some(s) => s.clone(),
        None => {
            // This case should never happen... but just in case
            all_settings.insert(guild.id, GuildSettings::from_existing(&guild));
            spin_mut(&all_settings, &guild.id).await.unwrap().clone()
        }
    };
    if let Channel::Guild(c) = msg.channel(&ctx.http).await? {
        c.send_message(&ctx.http, |m| {
            m.embed(|e| {
                settings.populate_embed(e);
                e
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
#[allowed_roles("Tournament Admin")]
#[description("Tests the setup of the server.")]
async fn test(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let all_settings = data.get::<GuildSettingsMapContainer>().unwrap().read().await;
    // Gets a copy of the setting. We don't want to a reference to the copy since creating what
    // needs to be created will trigger the hooks and update the shared settings object.
    let guild: Guild = msg.guild(&ctx.cache).unwrap();
    let settings: GuildSettings = match spin_mut(&all_settings, &guild.id).await {
        Some(s) => s.clone(),
        None => {
            // This case should never happen... but just in case
            all_settings.insert(guild.id, GuildSettings::from_existing(&guild));
            spin_mut(&all_settings, &guild.id).await.unwrap().clone()
        }
    };
    let tests = String::from("Judge Role Exists:\nAdmin Role Exists:\nPairings Channel Exists:\nSend Pairings:\nEdit Pairings:\nSend Embed:\nEdit Embed:\nMatches Category Exists:\nCreate VC:\nDelete VC:\nCreate TC:\nDelete TC:\nRole Created:\nRole Deleted:");
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
        Some(channel) => {
            test_results += "Passed\n";
            if let Channel::Guild(pairings_channel) = guild.channels.get(&channel.id).unwrap() {
                match pairings_channel
                    .send_message(&ctx.http, |m| m.content("Testing..."))
                    .await
                {
                    Err(_) => {
                        test_results += &"Failed - Couldn't send message.\n".repeat(4);
                    }
                    Ok(m) => {
                        test_results += "Passed\n";
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
                        test_results += "Passed\n";
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
            Some(channel) => {
                if let Channel::Category(matches_category) =
                    guild.channels.get(&channel.id).unwrap()
                {
                    test_results += "Passed\n";
                    if settings.make_vc {
                        match guild
                            .create_channel(&ctx.http, |c| {
                                c.name("Test VC")
                                    .kind(ChannelType::Voice)
                                    .category(channel.id)
                            })
                            .await
                        {
                            Ok(c) => {
                                test_results += "Passed\n";
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
                                c.name("Test TC")
                                    .kind(ChannelType::Text)
                                    .category(channel.id)
                            })
                            .await
                        {
                            Ok(c) => {
                                test_results += "Passed\n";
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

    if let Ok(mut r) = guild
        .create_role(&ctx.http, |r| r.mentionable(true).name("Setup Test"))
        .await
    {
        test_results += &"Passed\n";
        if let Ok(_) = r.delete(&ctx.http).await {
            test_results += &"Passed\n";
        } else {
            test_results += &"Failed - couldn't delete role\n";
        }
    } else {
        test_results += &"Failed - couldn't create role\n";
        test_results += &"Omitted - couldn't create role\n";
    }

    let mut response = msg.reply(&ctx.http, "\u{200b}").await?;
    response
        .edit(&ctx.http, |m| {
            m.embed(|e| {
                e.title("Test Results").fields(vec![
                    ("Tests", tests, true),
                    ("Results", test_results, true),
                ])
            })
        })
        .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[sub_commands(
    server,
    format,
    "deck_count",
    "require_checkin",
    "require_deck",
    pairing,
    scoring
)]
#[usage("<option name>")]
#[description("Changes the default tournament settings for new tournaments in the server.")]
async fn defaults(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    msg.reply(
        &ctx.http,
        "Please specify a subcommand in order to adjust settings.",
    )
    .await?;
    Ok(())
}
