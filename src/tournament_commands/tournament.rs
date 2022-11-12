use serenity::{
    framework::standard::{
        macros::{command, group},
        Args, CommandResult,
    },
    model::prelude::*,
    prelude::*,
};

use squire_lib::tournament::TournamentPreset;

use crate::{model::containers::GuildTournRegistryMapContainer, utils::spin_lock::spin_mut};

use super::{admin::*, player_commands::*, settings_commands::*};

#[group]
#[commands(tournament)]
pub struct TournamentCommands;

#[command("tournament")]
#[aliases("tourn", "T", "t")]
#[sub_commands(
    admin,
    create,
    settings,
    add_deck,
    confirm_result,
    decklist,
    decks,
    drop,
    list,
    match_result,
    name,
    ready,
    register,
    re_register,
    remove_deck,
    profile
)]
#[usage("<option>")]
#[description("Commands pretaining to tournaments.")]
async fn tournament(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    msg.reply(
        &ctx.http,
        "Please specify a subcommand. If you're unsure, use `!sb-help tournament`.",
    )
    .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[usage("<type>, <name>")]
#[example("swiss, 'New Tournament'")]
#[example("fluid, 'New Tournament'")]
#[allowed_roles("Tournament Admin")]
#[description("Adjust the settings of a specfic tournament.")]
async fn create(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    // Verify that the arguements are parsable and correct
    let preset = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(
                &ctx.http,
                "Please include a tournament type, either 'swiss' or 'fluid'",
            )
            .await?;
            return Ok(());
        }
        Ok(s) => match s.to_lowercase().as_str() {
            "fluid" => TournamentPreset::Fluid,
            "swiss" => TournamentPreset::Swiss,
            _ => {
                msg.reply(
                    &ctx.http,
                    "Invalid tournament preset. The valid options are 'fluid' and 'swiss'.",
                )
                .await?;
                return Ok(());
            }
        },
    };
    let name = args.rest().trim().to_string();
    if name.is_empty() {
        msg.reply(&ctx.http, "Please include a name for the tournament.")
            .await?;
        return Ok(());
    }
    let data = ctx.data.read().await;
    let tourn_regs = data
        .get::<GuildTournRegistryMapContainer>()
        .unwrap()
        .read()
        .await;
    let g_id = msg.guild_id.unwrap();
    let mut reg = spin_mut(&tourn_regs, &g_id).await.unwrap();
    // Ensure that tournaments can be ran
    if !reg.settings.is_configured() {
        msg.reply(
            &ctx.http, "This server isn't configured to run tournaments. Use the `!setup` command to help you with this.",
        )
            .await?;
        return Ok(());
    }
    let guild = msg.guild(&ctx.cache).unwrap();
    // Create the role that the tournament will be using
    let tourn_role = match guild
        .create_role(&ctx.http, |r| {
            r.mentionable(true).name(format!("{name} Player"))
        })
        .await
    {
        Ok(role) => role,
        Err(_) => {
            msg.reply(&ctx.http, "Unable to create a role for the tournament.")
                .await?;
            return Ok(());
        }
    };

    let content = match reg.create_tourn(tourn_role, preset, name).await {
        true => "Tournament successfully created!!",
        false => "Could not create tournament!!",
    };
    msg.reply(&ctx.http, content).await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[sub_commands(
    format,
    deck_count,
    require_checkin,
    require_deck,
    round_length,
    pairings,
    scoring,
    discord
)]
#[usage("<option>")]
#[allowed_roles("Tournament Admin")]
#[description("Adjust the settings of a specfic tournament.")]
async fn settings(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    msg.reply(
        &ctx.http,
        "Please specify a subcommand in order to adjust settings.",
    )
    .await?;
    Ok(())
}
