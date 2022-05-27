use std::slice::SliceIndex;

use crate::{
    model::containers::GuildSettingsMapContainer,
    utils::{extract_id::extract_id, stringify::bool_from_string},
};

use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[sub_commands("pairings_channel", "matches_category", "create_vc", "create_text")]
#[min_args(1)]
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
#[min_args(1)]
#[description("Sets the default channel where future tournament will post pairings in.")]
async fn pairings_channel(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let arg = args.single::<String>().unwrap();
    let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
    let guild: Guild = msg.guild(&ctx.cache).unwrap();
    let mut settings = all_settings.get_mut(&guild.id).unwrap();
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
#[min_args(1)]
#[description(
    "Sets the default category where future tournament will create channels for matches."
)]
async fn matches_category(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let arg = args.single::<String>().unwrap();
    let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
    let guild: Guild = msg.guild(&ctx.cache).unwrap();
    let mut settings = all_settings.get_mut(&guild.id).unwrap();
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
#[min_args(1)]
#[description(
    "Toggles whether or not voice channels will be created for each match of future tournaments."
)]
async fn create_vc(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let arg = args.single::<String>().unwrap();
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
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
#[aliases("create-test")]
#[min_args(1)]
#[description(
    "Toggles whether or not text channels will be created for each match of future tournaments."
)]
async fn create_text(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let data = ctx.data.read().await;
    let arg = args.single::<String>().unwrap();
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
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
#[min_args(1)]
#[description("Adjusts the default format for future tournaments.")]
async fn format(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::TournamentSetting::*;
    let data = ctx.data.read().await;
    match args.single::<String>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings.tourn_settings.format = Format(val);
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
#[min_args(1)]
#[description("Adjusts the required deck count for future tournaments.")]
async fn min(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::TournamentSetting::*;
    let data = ctx.data.read().await;
    match args.single::<u8>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings.tourn_settings.min_deck_count = MinDeckCount(val);
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
#[min_args(1)]
#[description("Adjusts the required deck count for future tournaments.")]
async fn max(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::TournamentSetting::*;
    let data = ctx.data.read().await;
    match args.single::<u8>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings.tourn_settings.max_deck_count = MaxDeckCount(val);
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
#[min_args(1)]
#[description(
    "Toggles whether or not players must sign in before a tournament for future tournaments."
)]
async fn require_checkin(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::TournamentSetting::*;
    let data = ctx.data.read().await;
    let arg = args.single::<String>().unwrap();
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings.tourn_settings.require_check_in = RequireCheckIn(b);
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
#[min_args(1)]
#[description("Toggles whether or not decks must be registered for future tournaments.")]
async fn require_deck(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::TournamentSetting::*;
    let data = ctx.data.read().await;
    let arg = args.single::<String>().unwrap();
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings.tourn_settings.require_deck_reg = RequireDeckReg(b);
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
#[sub_commands(swiss, fluid)]
#[min_args(1)]
#[delimiters(",")]
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
#[sub_commands("swiss_match_size", "do_checkins")]
#[min_args(1)]
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
#[aliases("match-size")]
#[min_args(1)]
#[description("Sets the default match size for future swiss tournaments.")]
async fn swiss_match_size(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::SwissPairingsSetting::*;
    let data = ctx.data.read().await;
    match args.single::<u8>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings.tourn_settings.pairing_settings.swiss.match_size = MatchSize(val);
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
#[aliases("do-checkins")]
#[min_args(1)]
#[description(
    "Toggles the default for whether or not players must sign in before each match in future swiss tournaments."
)]
async fn do_checkins(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::SwissPairingsSetting::*;
    let data = ctx.data.read().await;
    let arg = args.single::<String>().unwrap();
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings.tourn_settings.pairing_settings.swiss.do_checkins = DoCheckIns(b);
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
#[sub_commands("fluid_match_size")]
#[min_args(1)]
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
#[aliases("match-size")]
#[min_args(1)]
#[description("Sets the default match size for future fluid-round tournaments.")]
async fn fluid_match_size(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::FluidPairingsSetting::*;
    let data = ctx.data.read().await;
    match args.single::<u8>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings.tourn_settings.pairing_settings.fluid.match_size = MatchSize(val);
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
#[sub_commands("standard")]
#[min_args(1)]
#[delimiters(",")]
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
#[min_args(1)]
#[description("")]
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
#[min_args(1)]
#[description("")]
async fn match_win_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    match args.single::<f64>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings
                .tourn_settings
                .scoring_settings
                .standard
                .match_win_points = MatchWinPoints(val);
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
#[min_args(1)]
#[description("")]
async fn match_draw_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    match args.single::<f64>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings
                .tourn_settings
                .scoring_settings
                .standard
                .match_draw_points = MatchDrawPoints(val);
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
#[min_args(1)]
#[description("")]
async fn match_loss_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    match args.single::<f64>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings
                .tourn_settings
                .scoring_settings
                .standard
                .match_loss_points = MatchLossPoints(val);
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
#[min_args(1)]
#[description("")]
async fn game_win_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    match args.single::<f64>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings
                .tourn_settings
                .scoring_settings
                .standard
                .game_win_points = GameWinPoints(val);
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
#[min_args(1)]
#[description("")]
async fn game_draw_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    match args.single::<f64>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings
                .tourn_settings
                .scoring_settings
                .standard
                .game_draw_points = GameDrawPoints(val);
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
#[min_args(1)]
#[description("")]
async fn game_loss_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    match args.single::<f64>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings
                .tourn_settings
                .scoring_settings
                .standard
                .game_loss_points = GameLossPoints(val);
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
#[min_args(1)]
#[description("")]
async fn bye_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    match args.single::<f64>() {
        Ok(val) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings.tourn_settings.scoring_settings.standard.bye_points = ByePoints(val);
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
#[min_args(1)]
#[description("")]
async fn include_byes(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    let arg = args.single::<String>().unwrap();
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings
                .tourn_settings
                .scoring_settings
                .standard
                .include_byes = IncludeByes(b);
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
#[min_args(1)]
#[description("")]
async fn include_match_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    let arg = args.single::<String>().unwrap();
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings
                .tourn_settings
                .scoring_settings
                .standard
                .include_match_points = IncludeMatchPoints(b);
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
#[min_args(1)]
#[description("")]
async fn include_game_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    let arg = args.single::<String>().unwrap();
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings
                .tourn_settings
                .scoring_settings
                .standard
                .include_game_points = IncludeGamePoints(b);
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
#[min_args(1)]
#[description("")]
async fn include_mwp(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    let arg = args.single::<String>().unwrap();
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings
                .tourn_settings
                .scoring_settings
                .standard
                .include_mwp = IncludeMwp(b);
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
#[min_args(1)]
#[description("")]
async fn include_gwp(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    let arg = args.single::<String>().unwrap();
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings
                .tourn_settings
                .scoring_settings
                .standard
                .include_gwp = IncludeGwp(b);
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
#[min_args(1)]
#[description("")]
async fn include_opp_mwp(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    let arg = args.single::<String>().unwrap();
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings
                .tourn_settings
                .scoring_settings
                .standard
                .include_opp_mwp = IncludeOppMwp(b);
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
#[min_args(1)]
#[description("")]
async fn include_opp_gwp(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::StandardScoringSetting::*;
    let data = ctx.data.read().await;
    let arg = args.single::<String>().unwrap();
    match bool_from_string(&arg) {
        Some(b) => {
            let all_settings = data.get::<GuildSettingsMapContainer>().unwrap();
            let mut settings = all_settings.get_mut(&msg.guild_id.unwrap()).unwrap();
            settings
                .tourn_settings
                .scoring_settings
                .standard
                .include_opp_gwp = IncludeOppGwp(b);
        }
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
        }
    }
    Ok(())
}
