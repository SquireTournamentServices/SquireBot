use serenity::{
    framework::standard::{macros::command, Args, CommandResult},
    model::prelude::*,
    prelude::*,
};

use squire_core::{operations::TournOp, player_registry::PlayerIdentifier};

use crate::{
    model::containers::{
        CardCollectionContainer, GuildAndTournamentIDMapContainer, TournamentMapContainer,
        TournamentNameAndIDMapContainer,
    },
    utils::{
        error_to_reply::error_to_reply,
        extract_id::extract_id,
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
    use squire_core::settings::TournamentSetting::*;
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
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
    let format = Format(raw_format);
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(format)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
    }
    Ok(())
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
    use squire_core::settings::TournamentSetting::*;
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let raw_setting = match args.single_quoted::<u8>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
            return Ok(());
        }
        Ok(n) => n,
    };
    let setting = MinDeckCount(raw_setting);
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("<count>, [tournament name]")]
#[example("10")]
#[min_args(1)]
#[description("Adjusts the required deck count for future tournaments.")]
async fn max(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::TournamentSetting::*;
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let raw_setting = match args.single_quoted::<u8>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
            return Ok(());
        }
        Ok(n) => n,
    };
    let setting = MaxDeckCount(raw_setting);
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
    }
    Ok(())
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
    use squire_core::settings::TournamentSetting::*;
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let raw_setting = match bool_from_string(&arg) {
        Some(b) => b,
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
    };
    let setting = RequireCheckIn(raw_setting);
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
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
    use squire_core::settings::TournamentSetting::*;
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let raw_setting = match bool_from_string(&arg) {
        Some(b) => b,
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
    };
    let setting = RequireDeckReg(raw_setting);
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[sub_commands(swiss, fluid)]
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
#[sub_commands("swiss_match_size", "do_checkins")]
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
#[aliases("match-size")]
#[usage("<size>, [tournament name]")]
#[example("4")]
#[min_args(1)]
#[description("Sets the default match size for future swiss tournaments.")]
async fn swiss_match_size(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::{PairingSetting::*, SwissPairingsSetting::*, TournamentSetting::*};
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let raw_setting = match args.single_quoted::<u8>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
            return Ok(());
        }
        Ok(n) => n,
    };
    let setting = PairingSetting(Swiss(MatchSize(raw_setting)));
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
    }
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
    use squire_core::settings::{PairingSetting::*, SwissPairingsSetting::*, TournamentSetting::*};
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let raw_setting = match bool_from_string(&arg) {
        Some(b) => b,
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
    };
    let setting = PairingSetting(Swiss(DoCheckIns(raw_setting)));
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[sub_commands("fluid_match_size")]
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
#[aliases("match-size")]
#[usage("<size>, [tournament name]")]
#[example("4")]
#[min_args(1)]
#[description("Sets the default match size for future fluid-round tournaments.")]
async fn fluid_match_size(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_core::settings::{FluidPairingsSetting::*, PairingSetting::*, TournamentSetting::*};
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let raw_setting = match args.single_quoted::<u8>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number.").await?;
            return Ok(());
        }
        Ok(n) => n,
    };
    let setting = PairingSetting(Fluid(MatchSize(raw_setting)));
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
    }
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
#[sub_commands(match_win_points,
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
    include_opp_gwp)]
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
    use squire_core::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let raw_setting = match args.single_quoted::<f64>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
                .await?;
            return Ok(());
        }
        Ok(n) => n,
    };
    let setting = ScoringSetting(Standard(MatchWinPoints(raw_setting)));
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
    }
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
    use squire_core::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let raw_setting = match args.single_quoted::<f64>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
                .await?;
            return Ok(());
        }
        Ok(n) => n,
    };
    let setting = ScoringSetting(Standard(MatchDrawPoints(raw_setting)));
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
    }
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
    use squire_core::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let raw_setting = match args.single_quoted::<f64>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
                .await?;
            return Ok(());
        }
        Ok(n) => n,
    };
    let setting = ScoringSetting(Standard(MatchLossPoints(raw_setting)));
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
    }
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
    use squire_core::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let raw_setting = match args.single_quoted::<f64>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
                .await?;
            return Ok(());
        }
        Ok(n) => n,
    };
    let setting = ScoringSetting(Standard(GameWinPoints(raw_setting)));
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
    }
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
    use squire_core::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let raw_setting = match args.single_quoted::<f64>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
                .await?;
            return Ok(());
        }
        Ok(n) => n,
    };
    let setting = ScoringSetting(Standard(GameDrawPoints(raw_setting)));
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
    }
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
    use squire_core::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let raw_setting = match args.single_quoted::<f64>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
                .await?;
            return Ok(());
        }
        Ok(n) => n,
    };
    let setting = ScoringSetting(Standard(GameLossPoints(raw_setting)));
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
    }
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
    use squire_core::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let raw_setting = match args.single_quoted::<f64>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify a number (can be a decimal).")
                .await?;
            return Ok(());
        }
        Ok(n) => n,
    };
    let setting = ScoringSetting(Standard(ByePoints(raw_setting)));
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
    }
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
    use squire_core::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let raw_setting = match bool_from_string(&arg) {
        Some(b) => b,
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
    };
    let setting = ScoringSetting(Standard(IncludeByes(raw_setting)));
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
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
    use squire_core::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let raw_setting = match bool_from_string(&arg) {
        Some(b) => b,
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
    };
    let setting = ScoringSetting(Standard(IncludeMatchPoints(raw_setting)));
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
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
    use squire_core::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let raw_setting = match bool_from_string(&arg) {
        Some(b) => b,
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
    };
    let setting = ScoringSetting(Standard(IncludeGamePoints(raw_setting)));
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
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
    use squire_core::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let raw_setting = match bool_from_string(&arg) {
        Some(b) => b,
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
    };
    let setting = ScoringSetting(Standard(IncludeMwp(raw_setting)));
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
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
    use squire_core::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let raw_setting = match bool_from_string(&arg) {
        Some(b) => b,
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
    };
    let setting = ScoringSetting(Standard(IncludeGwp(raw_setting)));
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
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
    use squire_core::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let raw_setting = match bool_from_string(&arg) {
        Some(b) => b,
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
    };
    let setting = ScoringSetting(Standard(IncludeOppMwp(raw_setting)));
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
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
    use squire_core::settings::{
        ScoringSetting::*, StandardScoringSetting::*, TournamentSetting::*,
    };
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let raw_setting = match bool_from_string(&arg) {
        Some(b) => b,
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
    };
    let setting = ScoringSetting(Standard(IncludeOppGwp(raw_setting)));
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Err(err) = tourn.tourn.apply_op(TournOp::UpdateTournSetting(setting)) {
        error_to_reply(ctx, msg, err).await?;
    } else {
        tourn.update_status = true;
        msg.reply(&ctx.http, "Setting successfully updated!")
            .await?;
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
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
    let guild: Guild = msg.guild(&ctx.cache).unwrap();
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
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Some(channel) = guild.channels.get(&channel_id) {
        match channel {
            Channel::Guild(c) => {
                if c.kind == ChannelType::Text {
                    tourn.pairings_channel = c.clone();
                    tourn.update_status = true;
                    msg.reply(&ctx.http, "Pairings channel updated.").await?;
                } else {
                    msg.reply(&ctx.http, "Please specify a text channel.")
                        .await?;
                }
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
#[usage("<category name/mention>, [tournament name]")]
#[example("'matches'")]
#[example("#matches")]
#[min_args(1)]
#[description(
    "Sets the default category where future tournament will create channels for matches."
)]
async fn matches_category(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
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
    let guild: Guild = msg.guild(&ctx.cache).unwrap();
    let channel_id = match extract_id(&arg) {
        Some(id) => ChannelId(id),
        None => match guild.channel_id_from_name(&ctx.cache, arg) {
            Some(id) => id,
            None => {
                msg.reply(
                    &ctx.http,
                    "Please include a category, either by name or mention.",
                )
                .await?;
                return Ok(());
            }
        },
    };
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    if let Some(channel) = guild.channels.get(&channel_id) {
        match channel {
            Channel::Category(c) => {
                tourn.matches_category = c.clone();
                tourn.update_status = true;
                msg.reply(&ctx.http, "Matches category updated.").await?;
            }
            _ => {
                msg.reply(&ctx.http, "Please specify a category channel.")
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
#[aliases("create-vc")]
#[usage("<true/false>, [tournament name]")]
#[min_args(1)]
#[description(
    "Toggles whether or not voice channels will be created for each match of future tournaments."
)]
async fn create_vc(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let setting = match bool_from_string(&arg) {
        Some(b) => b,
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
    };
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    tourn.update_status = true;
    tourn.make_vc = setting;
    msg.reply(&ctx.http, "Setting successfully updated!")
        .await?;
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
    let all_tourns = data.get::<TournamentMapContainer>().unwrap();
    let mut id_iter = ids.get_left_iter(&msg.guild_id.unwrap()).unwrap().cloned();
    // Resolve the tournament id
    let arg = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let setting = match bool_from_string(&arg) {
        Some(b) => b,
        None => {
            msg.reply(&ctx.http, "Please specify 'true' or 'false'.")
                .await?;
            return Ok(());
        }
    };
    let tourn_name = args.rest().trim().to_string();
    let tourn_id = match admin_tourn_id_resolver(ctx, msg, &tourn_name, &name_and_id, id_iter).await
    {
        Some(id) => id,
        None => {
            return Ok(());
        }
    };
    let mut tourn = all_tourns.get_mut(&tourn_id).unwrap();
    tourn.update_status = true;
    tourn.make_tc = setting;
    msg.reply(&ctx.http, "Setting successfully updated!")
        .await?;
    Ok(())
}
