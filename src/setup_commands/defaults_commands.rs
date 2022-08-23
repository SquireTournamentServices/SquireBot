use std::slice::SliceIndex;

use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_lib::{
    pairings::PairingAlgorithm,
    settings::{PairingSetting, StandardScoringSetting, TournamentSetting},
};

use crate::{
    model::containers::GuildSettingsMapContainer,
    utils::{extract_id::extract_id, spin_lock::spin_mut, stringify::bool_from_string},
};

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[sub_commands("pairings_channel", "matches_category", "create_vc", "create_tc")]
#[usage("<option name>")]
#[description("Adjusts the default ways future tournaments will interact with this server.")]
async fn server(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    msg.reply(
        &ctx.http,
        "Please specify a subcommand in order to adjust settings.",
    )
    .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("pairings-channel")]
#[usage("<channel name/mention>")]
#[example("'look-matches'")]
#[example("#look-matches")]
#[min_args(1)]
#[description("Sets the default channel where future tournament will post pairings in.")]
async fn pairings_channel(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(
                &ctx.http,
                "Please include a channel, either by name or mention.",
            )
            .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
    let guild: Guild = msg.guild(&ctx.cache).unwrap();
    let mut settings = spin_mut(all_settings, &guild.id).await.unwrap();
    let channel_id = match extract_id(&arg) {
        Some(id) => ChannelId(id),
        None => match guild.channel_id_from_name(&ctx.cache, arg) {
            Some(id) => id,
            None => {
                msg.reply(
                    &ctx.http,
                    "Please include a channel, either by name or mention.",
                )
                .await?;
                return Ok(());
            }
        },
    };
    if let Some(channel) = guild.channels.get(&channel_id) {
        match channel {
            Channel::Guild(c) => {
                settings.pairings_channel = Some(c.clone());
                msg.reply(&ctx.http, "Default pairings channel updated.")
                    .await?;
            }
            _ => {
                msg.reply(&ctx.http, "Please specify a text channel.")
                    .await?;
            }
        }
    } else {
        msg.reply(&ctx.http, "Please specify an active channel in this guild.")
            .await?;
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("matches-category")]
#[usage("<category name/mention>")]
#[example("'game-channels'")]
#[example("#game-channels")]
#[min_args(1)]
#[description(
    "Sets the default category where future tournament will create channels for matches."
)]
async fn matches_category(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(
                &ctx.http,
                "Please include a category, either by name or mention.",
            )
            .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
    let guild: Guild = msg.guild(&ctx.cache).unwrap();
    let mut settings = spin_mut(all_settings, &guild.id).await.unwrap();
    let channel_id = match extract_id(&arg) {
        Some(id) => ChannelId(id),
        None => match guild.channel_id_from_name(&ctx.cache, arg) {
            Some(id) => id,
            None => {
                msg.reply(
                    &ctx.http,
                    "Please include a channel, either by name or mention.",
                )
                .await?;
                return Ok(());
            }
        },
    };
    if let Some(channel) = guild.channels.get(&channel_id) {
        match channel {
            Channel::Category(c) => {
                settings.matches_category = Some(c.clone());
                msg.reply(&ctx.http, "Default matches category updated.")
                    .await?;
            }
            _ => {
                msg.reply(&ctx.http, "Please specify a category.").await?;
            }
        }
    } else {
        msg.reply(
            &ctx.http,
            "Please specify an active category in this guild.",
        )
        .await?;
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("create-vc")]
#[usage("<true/false>")]
#[example("true")]
#[min_args(1)]
#[description(
    "Toggles whether or not voice channels will be created for each match of future tournaments."
)]
async fn create_vc(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings.make_vc = b;
        }
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("create-tc")]
#[usage("<true/false>")]
#[example("true")]
#[min_args(1)]
#[description(
    "Toggles whether or not text channels will be created for each match of future tournaments."
)]
async fn create_tc(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings.make_tc = b;
        }
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[sub_commands(
    format,
    "deck_count",
    "require_checkin",
    "require_deck",
    pairing,
    scoring
)]
#[aliases("tourn")]
#[usage("<option>")]
#[min_args(1)]
#[description("Adjusts the defaults for future tournaments.")]
async fn tournament(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    msg.reply(
        &ctx.http,
        "Please specify a subcommand in order to adjust settings.",
    )
    .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("format <name>")]
#[example("cEDH")]
#[min_args(1)]
#[description("Adjusts the default format for future tournaments.")]
async fn format(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::TournamentSetting::*;
    let data = ctx.data.read().await;
    match args.single_quoted::<String>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(TournamentSetting::Format(val));
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a your default format.")
                .await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("deck-count")]
#[sub_commands(min, max)]
#[usage("<min/max>")]
#[description("Adjusts the required deck count for future tournaments.")]
async fn deck_count(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    msg.reply(
        &ctx.http,
        "Please specify a subcommand in order to adjust settings.",
    )
    .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("min <count>")]
#[example("1")]
#[min_args(1)]
#[description("Adjusts the required deck count for future tournaments.")]
async fn min(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::TournamentSetting::*;
    let data = ctx.data.read().await;
    match args.single_quoted::<u8>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(TournamentSetting::MinDeckCount(val));
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("<count>")]
#[example("10")]
#[min_args(1)]
#[description("Adjusts the required deck count for future tournaments.")]
async fn max(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::TournamentSetting::*;
    let data = ctx.data.read().await;
    match args.single_quoted::<u8>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(TournamentSetting::MaxDeckCount(val));
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("require-checkin")]
#[usage("<true/false>")]
#[min_args(1)]
#[description(
    "Toggles whether or not players must sign in before a tournament for future tournaments."
)]
async fn require_checkin(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::TournamentSetting::*;
    let data = ctx.data.read().await;
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(RequireCheckIn(b).into());
        }
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("require-deck")]
#[usage("<true/false>")]
#[min_args(1)]
#[description("Toggles whether or not decks must be registered for future tournaments.")]
async fn require_deck(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::TournamentSetting::*;
    let data = ctx.data.read().await;
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(RequireDeckReg(b).into());
        }
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[sub_commands(algorithm, match_size, repair_tolerance, swiss, fluid)]
#[usage("<option>")]
#[description("Adjusts the default pairing settings for future tournament.")]
async fn pairing(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    msg.reply(
        &ctx.http,
        "Please specify a subcommand in order to adjust settings.",
    )
    .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("<alg>")]
#[example("Greedy")]
#[min_args(1)]
#[description("Sets the default pairings algorithm.")]
async fn algorithm(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let data = ctx.data.read().await;
    match args.single_quoted::<String>() {
        Ok(val) => match val.as_str() {
            "greedy" | "Greedy" => {
                let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
                let id = msg.guild_id.unwrap();
                let mut settings = spin_mut(all_settings, &id).await.unwrap();
                settings
                    .tourn_settings
                    .update_setting(PairingSetting::Algorithm(PairingAlgorithm::Greedy).into());
            }
            _ => {
                msg.reply(
                    &ctx.http,
                    "Please specify an algorithm. The options are:\nGreedy",
                )
                .await?;
            }
        },
        Err(_) => {
            msg.reply(
                &ctx.http,
                "Please specify an algorithm. The options are:\nGreedy",
            )
            .await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("match-size")]
#[usage("<size>")]
#[example("4")]
#[min_args(1)]
#[description("Sets the default match size for future swiss tournaments.")]
async fn match_size(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::SwissPairingsSetting::*;
    let data = ctx.data.read().await;
    match args.single_quoted::<u8>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(PairingSetting::MatchSize(val).into());
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("repair-tolerance")]
#[usage("<number>")]
#[example("1")]
#[min_args(1)]
#[description("Sets the default number of repaired pairs of players that are acceptable for new rounds.")]
async fn repair_tolerance(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let data = ctx.data.read().await;
    match args.single_quoted::<u64>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(PairingSetting::RepairTolerance(val).into());
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[sub_commands("do_checkins")]
#[usage("<option>")]
#[description("Adjusts the default swiss pairing settings for future tournament.")]
async fn swiss(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    msg.reply(
        &ctx.http,
        "Please specify a subcommand in order to adjust settings.",
    )
    .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("do-checkins")]
#[usage("<true/false>")]
#[min_args(1)]
#[description(
    "Toggles the default for whether or not players must sign in before each match in future swiss tournaments."
)]
async fn do_checkins(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::SwissPairingsSetting::*;
    let data = ctx.data.read().await;
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            let setting: PairingSetting = DoCheckIns(b).into();
            settings.tourn_settings.update_setting(setting.into());
        }
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("<option>")]
#[description("Adjusts the default fluid-round pairing settings for future tournament.")]
async fn fluid(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    msg.reply(
        &ctx.http,
        "Please specify a subcommand in order to adjust settings.",
    )
    .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[sub_commands("standard")]
#[usage("<option>")]
#[description("Adjusts the default settings for future tournament that pretain to scoring.")]
async fn scoring(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    msg.reply(
        &ctx.http,
        "Please specify a subcommand in order to adjust settings.",
    )
    .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[sub_commands(
    match_win_points,
    match_draw_points,
    match_loss_points,
    game_win_points,
    game_draw_points,
    game_loss_points,
    bye_points,
    include_byes,
    include_match_points,
    include_game_points,
    include_mwp,
    include_gwp,
    include_opp_mwp,
    include_opp_gwp
)]
#[usage("<option>")]
#[description(
    "Adjusts the default settings for future tournament that use the standard scoring model."
)]
async fn standard(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    msg.reply(
        &ctx.http,
        "Please specify a subcommand in order to adjust settings.",
    )
    .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("match-win-points")]
#[usage("<points>")]
#[example("3.5")]
#[min_args(1)]
#[description("Adjusts the default number of points that winning a match is worth (can be any decimal number).")]
async fn match_win_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    match args.single_quoted::<f64>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(MatchWinPoints(val).into());
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("match-draw-points")]
#[usage("<points>")]
#[example("1")]
#[min_args(1)]
#[description("Adjusts the default number of points that drawing a match is worth (can be any decimal number).")]
async fn match_draw_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    match args.single_quoted::<f64>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(MatchDrawPoints(val).into());
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("match-loss-points")]
#[usage("<points>")]
#[example("-0.5")]
#[min_args(1)]
#[description("Adjusts the default number of points that lossing a match is worth (can be any decimal number).")]
async fn match_loss_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    match args.single_quoted::<f64>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(MatchLossPoints(val).into());
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("game-win-points")]
#[usage("<points>")]
#[example("1")]
#[min_args(1)]
#[description("Adjusts the default number of points that drawing a game is worth (can be any decimal number).")]
async fn game_win_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    match args.single_quoted::<f64>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(GameWinPoints(val).into());
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("game-draw-points")]
#[usage("<points>")]
#[example("0.5")]
#[min_args(1)]
#[description("Adjusts the default number of points that drawing a game is worth (can be any decimal number).")]
async fn game_draw_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    match args.single_quoted::<f64>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(GameDrawPoints(val).into());
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("game-loss-points")]
#[usage("<points>")]
#[example("0")]
#[min_args(1)]
#[description("Adjusts the default number of points that lossing a game is worth (can be any decimal number).")]
async fn game_loss_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    match args.single_quoted::<f64>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(GameLossPoints(val).into());
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("bye-points")]
#[usage("<points>")]
#[example("3")]
#[min_args(1)]
#[description(
    "Adjusts the default number of points that a byes is worth (can be any decimal number)."
)]
async fn bye_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    match args.single_quoted::<f64>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(ByePoints(val).into());
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-byes")]
#[usage("<true/false>")]
#[min_args(1)]
#[description("Adjusts where or not byes are used when calculating standings.")]
async fn include_byes(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(IncludeByes(b).into());
        }
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-match-points")]
#[usage("<true/false>")]
#[min_args(1)]
#[description("Adjusts the whether or not a player's match points are used in the standings.")]
async fn include_match_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(IncludeMatchPoints(b).into());
        }
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-game-points")]
#[usage("<true/false>")]
#[min_args(1)]
#[description("Adjusts the whether or not a player's game points are used in the standings.")]
async fn include_game_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(IncludeGamePoints(b).into());
        }
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-mwp")]
#[usage("<true/false>")]
#[min_args(1)]
#[description("Adjusts the whether or not a player's match win percent is used in the standings.")]
async fn include_mwp(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(IncludeMwp(b).into());
        }
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-gwp")]
#[usage("<true/false>")]
#[min_args(1)]
#[description("Adjusts the whether or not a player's game win percent is used in the standings.")]
async fn include_gwp(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(IncludeGwp(b).into());
        }
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-opp-mwp")]
#[usage("<true/false>")]
#[min_args(1)]
#[description("Adjusts the whether or not opponent match win percent is used in the standings.")]
async fn include_opp_mwp(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(IncludeOppMwp(b).into());
        }
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-opp-gwp")]
#[usage("<true/false>")]
#[min_args(1)]
#[description("Adjusts the whether or not opponent game win percent is used in the standings.")]
async fn include_opp_gwp(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let id = msg.guild_id.unwrap();
            let mut settings = spin_mut(all_settings, &id).await.unwrap();
            settings
                .tourn_settings
                .update_setting(IncludeOppGwp(b).into());
        }
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
        }
    }
    Ok(())
}
