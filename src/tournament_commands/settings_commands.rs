use std::time::Duration;

use serenity::{
    framework::standard::{macros::command, Args, CommandError, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_lib::{
    operations::TournOp, pairings::PairingAlgorithm, player_registry::PlayerIdentifier,
    settings::TournamentSetting,
};

use crate::{
    model::{
        consts::SQUIRE_ACCOUNT_ID,
        containers::{
            CardCollectionContainer, GuildAndTournamentIDMapContainer, TournamentMapContainer,
            TournamentNameAndIDMapContainer,
        },
        guild_tournament::SquireTournamentSetting,
    },
    utils::{
        error_to_reply::error_to_reply,
        extract_id::extract_id,
        spin_lock::spin_mut,
        stringify::bool_from_string,
        tourn_resolver::{admin_tourn_id_resolver, user_id_resolver},
    },
};

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("<format name>, [tournament name]")]
#[example("cEDH")]
#[min_args(1)]
#[description("Adjusts the default format for future tournaments.")]
async fn format(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::TournamentSetting::*;
    let raw_format = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please include the name of a format.")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    if raw_format.len() == 0 {
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
#[usage("min <count>, [tournament name]")]
#[example("1")]
#[min_args(1)]
#[description("Adjusts the required deck count for future tournaments.")]
async fn min(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::TournamentSetting::*;
    let data = ctx.data.read().await;
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
    use squire_lib::settings::TournamentSetting::*;
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
    use squire_lib::settings::TournamentSetting::*;
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
    use squire_lib::settings::TournamentSetting::*;
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
    use squire_lib::settings::TournamentSetting::*;
    match args.single_quoted::<u64>() {
        Ok(dur) => {
            let setting = RoundLength(Duration::from_secs(dur * 60)).into();
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
    use squire_lib::settings::{PairingSetting::*, TournamentSetting::*};
    match args.single_quoted::<u8>() {
        Ok(n) => {
            let setting: TournamentSetting = MatchSize(n).into();
            settings_command(ctx, msg, setting.into(), args.rest().trim().to_string()).await
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
    use squire_lib::settings::{PairingSetting::*, TournamentSetting::*};
    match args.single_quoted::<u64>() {
        Ok(n) => {
            let setting: TournamentSetting = RepairTolerance(n).into();
            settings_command(ctx, msg, setting.into(), args.rest().trim().to_string()).await
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
    use squire_lib::settings::{PairingSetting::*, TournamentSetting::*};
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
            let setting: TournamentSetting = Algorithm(alg).into();
            settings_command(ctx, msg, setting.into(), args.rest().trim().to_string()).await
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
async fn swiss(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    use squire_lib::settings::{PairingSetting::*, SwissPairingsSetting::*, TournamentSetting::*};
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        let setting = PairingSetting(Swiss(DoCheckIns(b))).into();
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
async fn fluid(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
async fn standard(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    use squire_lib::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
    match args.single_quoted::<f64>() {
        Ok(n) => {
            let setting = ScoringSetting(Standard(MatchWinPoints(n))).into();
            settings_command(ctx, msg, setting, args.rest().trim().to_string()).await
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
                .await?;
            Ok(())
        }
    }
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
    use squire_lib::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
    match args.single_quoted::<f64>() {
        Ok(n) => {
            let setting = ScoringSetting(Standard(MatchDrawPoints(n))).into();
            settings_command(ctx, msg, setting, args.rest().trim().to_string()).await
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
                .await?;
            Ok(())
        }
    }
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
    use squire_lib::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
    match args.single_quoted::<f64>() {
        Ok(n) => {
            let setting = ScoringSetting(Standard(MatchLossPoints(n))).into();
            settings_command(ctx, msg, setting, args.rest().trim().to_string()).await
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
                .await?;
            Ok(())
        }
    }
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
    use squire_lib::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
    match args.single_quoted::<f64>() {
        Ok(n) => {
            let setting = ScoringSetting(Standard(GameWinPoints(n))).into();
            settings_command(ctx, msg, setting, args.rest().trim().to_string()).await
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
                .await?;
            return Ok(());
        }
    }
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
    use squire_lib::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
    match args.single_quoted::<f64>() {
        Ok(n) => {
            let setting = ScoringSetting(Standard(GameDrawPoints(n))).into();
            settings_command(ctx, msg, setting, args.rest().trim().to_string()).await
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
                .await?;
            Ok(())
        }
    }
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
    use squire_lib::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
    match args.single_quoted::<f64>() {
        Ok(n) => {
            let setting = ScoringSetting(Standard(GameLossPoints(n))).into();
            settings_command(ctx, msg, setting, args.rest().trim().to_string()).await
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
                .await?;
            Ok(())
        }
    }
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
    use squire_lib::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
    match args.single_quoted::<f64>() {
        Ok(n) => {
            let setting = ScoringSetting(Standard(ByePoints(n))).into();
            settings_command(ctx, msg, setting, args.rest().trim().to_string()).await
        }
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
                .await?;
            Ok(())
        }
    }
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-byes")]
#[usage("<true/false>, [tournament name]")]
#[min_args(1)]
#[description("Toggle if byes are used in calculating scores.")]
async fn include_byes(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        let setting = ScoringSetting(Standard(IncludeByes(b))).into();
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
    use squire_lib::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        let setting = ScoringSetting(Standard(IncludeMatchPoints(b))).into();
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
    use squire_lib::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        let setting = ScoringSetting(Standard(IncludeGamePoints(b))).into();
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
    use squire_lib::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        let setting = ScoringSetting(Standard(IncludeMwp(b))).into();
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
    use squire_lib::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        let setting = ScoringSetting(Standard(IncludeGwp(b))).into();
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
    use squire_lib::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        let setting = ScoringSetting(Standard(IncludeOppMwp(b))).into();
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
    use squire_lib::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
    if let Some(b) = arg_to_bool(ctx, msg, &mut args).await? {
        let setting = ScoringSetting(Standard(IncludeOppGwp(b))).into();
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
    use crate::model::guild_tournament::SquireTournamentSetting::*;
    let guild = msg.guild(&ctx.cache).unwrap();
    let result = args
        .single_quoted::<String>()
        .map(|arg| {
            extract_id(&arg).map_or_else(
                || {
                    guild
                        .channel_id_from_name(&ctx.cache, arg)
                        .ok_or("Please include a channel, either by name or mention.")
                },
                |id| Ok(ChannelId(id)),
            )
        })
        .map_err(|_| "Please include a channel, either by name or mention.")
        .flatten();
    if let Ok(content) = result {
        msg.reply(&ctx.http, content).await?;
        return Ok(());
    }
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
    use crate::model::guild_tournament::SquireTournamentSetting::*;
    let guild = msg.guild(&ctx.cache).unwrap();
    let result = args
        .single_quoted::<String>()
        .map(|arg| {
            extract_id(&arg).map_or_else(
                || {
                    guild
                        .channel_id_from_name(&ctx.cache, arg)
                        .ok_or("Please include a channel, either by name or mention.")
                },
                |id| Ok(ChannelId(id)),
            )
        })
        .map_err(|_| "Please include a channel, either by name or mention.")
        .flatten();
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
    if let Ok(content) = result {
        msg.reply(&ctx.http, content).await?;
        return Ok(());
    }
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
    use crate::model::guild_tournament::SquireTournamentSetting::*;
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
    use crate::model::guild_tournament::SquireTournamentSetting::*;
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
    let name_and_id = data
        .get::<TournamentNameAndIDMapContainer>()
        .unwrap()
        .read()
        .await;
    let ids = data
        .get::<GuildAndTournamentIDMapContainer>()
        .unwrap()
        .read()
        .await;
    let all_tourns = data.get::<TournamentMapContainer>().unwrap().read().await;
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = spin_mut(&all_tourns, &tourn_id).await.unwrap();
    if let Err(err) = tourn.update_setting(setting) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
    }
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
