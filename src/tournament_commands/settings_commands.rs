use std::{str::FromStr, time::Duration};

use num_rational::Rational32;
use serenity::{
    framework::standard::{macros::command, Args, CommandError, CommandResult},
    model::{mention::Mention, prelude::*},
    prelude::*,
};

use squire_lib::{pairings::PairingAlgorithm, settings::SwissPairingSetting};

use crate::{
    model::{containers::GuildTournRegistryMapContainer, guilds::SquireTournamentSetting},
    utils::{default_response::error_to_content, spin_lock::spin_mut, stringify::bool_from_string},
};

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("<format name>, [tournament name]")]
#[example("cEDH")]
#[min_args(1)]
#[description("Adjusts the default format for future tournaments.")]
async fn format(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use crate::squire_lib::settings::GeneralSetting::*;
    let raw_format = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please include the name of a format.")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    if raw_format.is_empty() {
        msg.reply(&ctx.http, "Please include the name of a format.")
            .await?;
        return Ok(());
    }

    let setting = Format(raw_format).into();
    settings_command(ctx, msg, setting, args.rest().trim().to_string()).await
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("deck-count")]
#[usage("<min/max>")]
#[sub_commands(min, max)]
#[description("Adjusts the required deck count for future tournaments.")]
async fn deck_count(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
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
#[usage("min <count>, [tournament name]")]
#[example("1")]
#[min_args(1)]
#[description("Adjusts the required deck count for future tournaments.")]
async fn min(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use crate::squire_lib::settings::GeneralSetting::*;
    let raw_setting = match args.single_quoted::<u8>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
            return Ok(());
        }
        Ok(n) => n,
    };

    let setting = MinDeckCount(raw_setting).into();
    settings_command(ctx, msg, setting, args.rest().trim().to_string()).await
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("<count>, [tournament name]")]
#[example("10")]
#[min_args(1)]
#[description("Adjusts the required deck count for future tournaments.")]
async fn max(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use crate::squire_lib::settings::GeneralSetting::*;
    let raw_setting = match args.single_quoted::<u8>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
            return Ok(());
        }
        Ok(n) => n,
    };
    let setting = MaxDeckCount(raw_setting).into();
    settings_command(ctx, msg, setting, args.rest().trim().to_string()).await
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("require-checkin")]
#[usage("<true/false>, [tournament name]")]
#[min_args(1)]
#[description(
    "Toggles whether or not players must sign in before a tournament for future tournaments."
)]
async fn require_checkin(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use crate::squire_lib::settings::GeneralSetting::*;
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        let setting = RequireCheckIn(b).into();

        settings_command(ctx, msg, setting, args.rest().trim().to_string()).await?;
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("require-deck")]
#[usage("<true/false>, [tournament name]")]
#[min_args(1)]
#[description("Toggles whether or not decks must be registered for future tournaments.")]
async fn require_deck(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use crate::squire_lib::settings::GeneralSetting::*;
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        let setting = RequireDeckReg(b).into();
        settings_command(ctx, msg, setting, args.rest().trim().to_string()).await?;
    }
    Ok(())
}

#[command("round_length")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("round-length")]
#[usage("<# of minutes>, [tournament name]")]
#[min_args(1)]
#[description("Adjusts the length of future rounds.")]
async fn round_length(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use crate::squire_lib::settings::GeneralSetting::*;
    match args.single_quoted::<u64>() {
        Ok(dur) => {
            let dur = Duration::from_secs(dur * 60);
            let setting = RoundLength(dur).into();
            settings_command(ctx, msg, setting, args.rest().trim().to_string()).await
        }
        Err(_) => {
            msg.reply(&ctx.http, "The number of minutes you want new round to be.")
                .await?;
            Ok(())
        }
    }
}

#[command]
#[only_in(guild)]
#[sub_commands(match_size, repair_tolerance, algorithm, swiss, fluid)]
#[allowed_roles("Tournament Admin")]
#[usage("<option>")]
#[description("Adjust the settings of a specfic tournament.")]
async fn pairings(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    msg.reply(&ctx.http, "Please specify a subcommand.").await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("match-size")]
#[usage("<size>, [tournament name]")]
#[example("4")]
#[min_args(1)]
#[description("Sets the default match size for future tournaments.")]
async fn match_size(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use crate::squire_lib::settings::CommonPairingSetting::*;
    match args.single_quoted::<u8>() {
        Ok(n) => {
            let setting = MatchSize(n).into();
            settings_command(ctx, msg, setting, args.rest().trim().to_string()).await
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
            Ok(())
        }
    }
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("repair-tolerance")]
#[usage("<size>, [tournament name]")]
#[example("4")]
#[min_args(1)]
#[description("Sets the default repair tolerance for matches in future tournaments.")]
async fn repair_tolerance(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use crate::squire_lib::settings::CommonPairingSetting::*;
    match args.single_quoted::<u64>() {
        Ok(n) => {
            let setting = RepairTolerance(n).into();
            settings_command(ctx, msg, setting, args.rest().trim().to_string()).await
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
            Ok(())
        }
    }
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("<size>, [tournament name]")]
#[example("4")]
#[min_args(1)]
#[description("Sets the default pairings algorithm for future tournaments.")]
async fn algorithm(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use crate::squire_lib::settings::CommonPairingSetting::*;
    match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
            return Ok(());
        }
        Ok(val) => {
            let alg = match val.as_str() {
                "greedy" | "Greedy" => PairingAlgorithm::Greedy,
                _ => {
                    msg.reply(
                        &ctx.http,
                        "Please specify an algorithm. The options are:\n - Greedy",
                    )
                    .await?;
                    return Ok(());
                }
            };
            let setting = Algorithm(alg).into();
            settings_command(ctx, msg, setting, args.rest().trim().to_string()).await
        }
    }
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[sub_commands("do_checkins")]
#[usage("<option>")]
#[min_args(1)]
#[description("Adjusts the default swiss pairing settings for future tournament.")]
async fn swiss(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    msg.reply(&ctx.http, "Please specify a subcommand.").await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("do-checkins")]
#[usage("<true/false>, [tournament name]")]
#[min_args(1)]
#[description(
    "Toggles the default for whether or not players must sign in before each match in future swiss tournaments."
)]
async fn do_checkins(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        let setting = SwissPairingSetting::DoCheckIns(b).into();
        settings_command(ctx, msg, setting, args.rest().trim().to_string()).await?;
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("<option>")]
#[min_args(1)]
#[description("Adjusts the default fluid-round pairing settings for future tournament.")]
async fn fluid(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    msg.reply(&ctx.http, "Please specify a subcommand.").await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[sub_commands("standard")]
#[usage("<option>")]
#[description("Adjusts how a tournament calculates scores.")]
async fn scoring(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    msg.reply(&ctx.http, "Please specify a subcommand.").await?;
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
#[description("Adjusts how a tournament calculates scores using the standard model.")]
async fn standard(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    msg.reply(&ctx.http, "Please specify a subcommand.").await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("match-win-points")]
#[usage("<points>, [tournament name]")]
#[example("3")]
#[min_args(1)]
#[description("Adjusts how many match points a match win is worth.")]
async fn match_win_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use crate::squire_lib::settings::StandardScoringSetting::*;
    if let Some(val) = args
        .single_quoted::<f64>()
        .ok()
        .and_then(Rational32::approximate_float)
    {
        let setting = MatchWinPoints(val).into();
        return settings_command(ctx, msg, setting, args.rest().trim().to_string()).await;
    }
    msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
        .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("match-draw-points")]
#[usage("<points>, [tournament name]")]
#[example("3")]
#[min_args(1)]
#[description("Adjusts how many match points a match win is worth.")]
async fn match_draw_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    if let Some(val) = args
        .single_quoted::<f64>()
        .ok()
        .and_then(Rational32::approximate_float)
    {
        let setting = MatchDrawPoints(val).into();
        return settings_command(ctx, msg, setting, args.rest().trim().to_string()).await;
    }
    msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
        .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("match-loss-points")]
#[usage("<points>, [tournament name]")]
#[example("3")]
#[min_args(1)]
#[description("Adjusts how many match points a match loss is worth.")]
async fn match_loss_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    if let Some(val) = args
        .single_quoted::<f64>()
        .ok()
        .and_then(Rational32::approximate_float)
    {
        let setting = MatchLossPoints(val).into();
        return settings_command(ctx, msg, setting, args.rest().trim().to_string()).await;
    }
    msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
        .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("game-win-points")]
#[usage("<points>, [tournament name]")]
#[example("1")]
#[min_args(1)]
#[description("Adjusts how many game points a game win is worth.")]
async fn game_win_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    if let Some(val) = args
        .single_quoted::<f64>()
        .ok()
        .and_then(Rational32::approximate_float)
    {
        let setting = GameWinPoints(val).into();
        return settings_command(ctx, msg, setting, args.rest().trim().to_string()).await;
    }
    msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
        .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("game-draw-points")]
#[usage("<points>, [tournament name]")]
#[example("1")]
#[min_args(1)]
#[description("Adjusts how many game points a game draw is worth.")]
async fn game_draw_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    if let Some(val) = args
        .single_quoted::<f64>()
        .ok()
        .and_then(Rational32::approximate_float)
    {
        let setting = GameDrawPoints(val).into();
        return settings_command(ctx, msg, setting, args.rest().trim().to_string()).await;
    }
    msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
        .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("game-loss-points")]
#[usage("<points>, [tournament name]")]
#[example("0")]
#[min_args(1)]
#[description("Adjusts how many game points a game loss is worth.")]
async fn game_loss_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    if let Some(val) = args
        .single_quoted::<f64>()
        .ok()
        .and_then(Rational32::approximate_float)
    {
        let setting = GameLossPoints(val).into();
        return settings_command(ctx, msg, setting, args.rest().trim().to_string()).await;
    }
    msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
        .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("bye-points")]
#[usage("<points>, [tournament name]")]
#[example("3")]
#[min_args(1)]
#[description("Adjusts how many match points a bye is worth.")]
async fn bye_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    if let Some(val) = args
        .single_quoted::<f64>()
        .ok()
        .and_then(Rational32::approximate_float)
    {
        let setting = ByePoints(val).into();
        return settings_command(ctx, msg, setting, args.rest().trim().to_string()).await;
    }
    msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
        .await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-byes")]
#[usage("<true/false>, [tournament name]")]
#[min_args(1)]
#[description("Toggle if byes are used in calculating scores.")]
async fn include_byes(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        let setting = IncludeByes(b).into();
        settings_command(ctx, msg, setting, args.rest().trim().to_string()).await?;
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-match-points")]
#[usage("<true/false>, [tournament name]")]
#[min_args(1)]
#[description("Toggle if match points are included in scores.")]
async fn include_match_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        let setting = IncludeMatchPoints(b).into();
        settings_command(ctx, msg, setting, args.rest().trim().to_string()).await?;
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-game-points")]
#[usage("<true/false>, [tournament name]")]
#[min_args(1)]
#[description("Toggle if game points are included in scores.")]
async fn include_game_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        let setting = IncludeGamePoints(b).into();
        settings_command(ctx, msg, setting, args.rest().trim().to_string()).await?;
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-mwp")]
#[usage("<true/false>, [tournament name]")]
#[min_args(1)]
#[description("Toggle if match win percent is included in scores.")]
async fn include_mwp(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        let setting = IncludeMwp(b).into();
        settings_command(ctx, msg, setting, args.rest().trim().to_string()).await?;
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-gwp")]
#[usage("<true/false>, [tournament name]")]
#[min_args(1)]
#[description("Toggle if game win percent is included in scores.")]
async fn include_gwp(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        let setting = IncludeGwp(b).into();
        settings_command(ctx, msg, setting, args.rest().trim().to_string()).await?;
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-opp-mwp")]
#[usage("<true/false>, [tournament name]")]
#[min_args(1)]
#[description("Toggle if opponent match win percent is included in scores.")]
async fn include_opp_mwp(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        let setting = IncludeOppMwp(b).into();
        settings_command(ctx, msg, setting, args.rest().trim().to_string()).await?;
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-opp-gwp")]
#[usage("<true/false>, [tournament name]")]
#[min_args(1)]
#[description("Toggle if opponent game win percent is included in scores.")]
async fn include_opp_gwp(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::StandardScoringSetting::*;
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        let setting = IncludeOppGwp(b).into();
        settings_command(ctx, msg, setting, args.rest().trim().to_string()).await?;
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[sub_commands("pairings_channel", "matches_category", "create_vc", "create_tc")]
#[usage("<option>")]
#[description("Adjust the Discord-specific settings of a tournament.")]
async fn discord(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    msg.reply(&ctx.http, "Please specify a subcommand.").await?;
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("pairings-channel")]
#[usage("<channel name/mention>, [tournament name]")]
#[example("'pairings'")]
#[example("#pairings")]
#[min_args(1)]
#[description("Sets the default channel where future tournament will post pairings in.")]
async fn pairings_channel(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use crate::model::guilds::SquireTournamentSetting::*;
    let guild = msg.guild(&ctx.cache).unwrap();
    let result = args
        .single_quoted::<String>()
        .map_err(|_| "Please include a channel, either by name or mention.")
        .and_then(|arg| match Mention::from_str(&arg).ok() {
            Some(Mention::Channel(id)) => Ok(id),
            Some(_) => Err("Please specify a channel, not a User, Role, or something"),
            None => match guild.channel_id_from_name(&ctx.cache, arg) {
                Some(id) => Ok(id),
                None => Err("Please include a channel, either by name or mention."),
            },
        });
    let response = match result {
        Err(content) => {
            msg.reply(&ctx.http, content).await?;
            None
        }
        Ok(channel_id) => match guild.channels.get(&channel_id) {
            Some(channel) => match channel {
                Channel::Guild(c) if c.kind == ChannelType::Text => {
                    let setting = PairingsChannel(c.clone());
                    settings_command(ctx, msg, setting, args.rest().trim().to_string()).await?;
                    None
                }
                _ => Some("Please specify a text channel."),
            },
            None => Some("Please specify an active channel in this guild."),
        },
    };
    if let Some(content) = response {
        msg.reply(&ctx.http, content).await?;
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("matches-category")]
#[usage("<category name/mention>, [tournament name]")]
#[example("'matches'")]
#[example("#matches")]
#[min_args(1)]
#[description(
    "Sets the default category where future tournament will create channels for matches."
)]
async fn matches_category(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use crate::model::guilds::SquireTournamentSetting::*;
    let guild = msg.guild(&ctx.cache).unwrap();
    let result = args
        .single_quoted::<String>()
        .map_err(|_| "Please include a channel, either by name or mention.")
        .and_then(|arg| match Mention::from_str(&arg).ok() {
            Some(Mention::Channel(id)) => Ok(id),
            Some(_) => Err("Please specify a channel, not a User, Role, or something"),
            None => match guild.channel_id_from_name(&ctx.cache, arg) {
                Some(id) => Ok(id),
                None => Err("Please include a channel, either by name or mention."),
            },
        });
    let response = match result {
        Err(content) => {
            msg.reply(&ctx.http, content).await?;
            None
        }
        Ok(channel_id) => match guild.channels.get(&channel_id) {
            Some(channel) => match channel {
                Channel::Category(c) => {
                    let setting = MatchesCategory(c.clone());
                    settings_command(ctx, msg, setting, args.rest().trim().to_string()).await?;
                    None
                }
                _ => Some("Please specify a category channel."),
            },
            None => Some("Please specify an active channel in this guild."),
        },
    };
    if let Some(content) = response {
        msg.reply(&ctx.http, content).await?;
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("create-vc")]
#[usage("<true/false>, [tournament name]")]
#[min_args(1)]
#[description(
    "Toggles whether or not voice channels will be created for each match of future tournaments."
)]
async fn create_vc(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use crate::model::guilds::SquireTournamentSetting::*;
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        settings_command(ctx, msg, CreateVC(b), args.rest().trim().to_string()).await?;
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("create-tc")]
#[usage("<true/false>, [tournament name]")]
#[min_args(1)]
#[description(
    "Toggles whether or not text channels will be created for each match of future tournaments."
)]
async fn create_tc(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use crate::model::guilds::SquireTournamentSetting::*;
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        settings_command(ctx, msg, CreateTC(b), args.rest().trim().to_string()).await?;
    }
    Ok(())
}

async fn settings_command(
    ctx: &Context,
    msg: &Message,
    setting: SquireTournamentSetting,
    tourn_name: String,
) -> CommandResult {
    let data = ctx.data.read().await;
    let tourn_regs = data
        .get::<GuildTournRegistryMapContainer>()
        .unwrap()
        .read()
        .await;
    let g_id = msg.guild_id.unwrap();
    let mut reg = spin_mut(&tourn_regs, &g_id).await.unwrap();
    let tourn = match reg.get_tourn_mut(&tourn_name) {
        Some(t) => t,
        None => {
            msg.reply(&ctx.http, "That tournament could not be found.")
                .await?;
            return Ok(());
        }
    };
    let content = match tourn.update_setting(setting) {
        Ok(_) => "Setting successfully updated!",
        Err(err) => error_to_content(err),
    };
    msg.reply(&ctx.http, content).await?;
    Ok(())
}

async fn arg_to_bool(
    ctx: &Context,
    msg: &Message,
    args: &mut Args,
) -> Result<Option<bool>, CommandError> {
    parse_arg(
        ctx,
        msg,
        args,
        bool_from_string,
        "Please specify 'true' or 'false'.",
    )
    .await
}

async fn parse_arg<F, T>(
    ctx: &Context,
    msg: &Message,
    args: &mut Args,
    f: F,
    err_msg: &str,
) -> Result<Option<T>, CommandError>
where
    F: FnOnce(&str) -> Option<T>,
{
    match args.single_quoted::<String>().map(|s| f(s.as_str())) {
        Ok(Some(s)) => Ok(Some(s)),
        _ => {
            msg.reply(&ctx.http, err_msg).await?;
            Ok(None)
        }
    }
}
