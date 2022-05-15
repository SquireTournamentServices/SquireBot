use crate::model::consts::*;

use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[sub_commands("pairings_channel", "matches_category", "create_vc", "create_text")]
#[min_args(1)]
#[description("Adjusts the default ways future tournaments will interact with this server.")]
async fn server(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("pairings-channel")]
#[min_args(1)]
#[description("Sets the default channel where future tournament will post pairings in.")]
async fn pairings_channel(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
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
    todo!()
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
    todo!()
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
    todo!()
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
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[min_args(1)]
#[description("Adjusts the default format for future tournaments.")]
async fn format(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("deck-count")]
#[sub_commands(min, max)]
#[description("Adjusts the required deck count for future tournaments.")]
async fn deck_count(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[min_args(1)]
#[description("Adjusts the required deck count for future tournaments.")]
async fn min(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[min_args(1)]
#[description("Adjusts the required deck count for future tournaments.")]
async fn max(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
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
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("require-deck")]
#[min_args(1)]
#[description("Toggles whether or not decks must be registered for future tournaments.")]
async fn require_deck(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[sub_commands(swiss, fluid)]
#[min_args(1)]
#[delimiters(",")]
#[description("Adjusts the default pairing settings for future tournament.")]
async fn pairing(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[sub_commands("swiss_match_size", "do_checkins")]
#[min_args(1)]
#[description("Adjusts the default swiss pairing settings for future tournament.")]
async fn swiss(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("match-size")]
#[min_args(1)]
#[description("Sets the default match size for future swiss tournaments.")]
async fn swiss_match_size(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
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
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[sub_commands("fluid_match_size")]
#[min_args(1)]
#[description("Adjusts the default fluid-round pairing settings for future tournament.")]
async fn fluid(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("match-size")]
#[min_args(1)]
#[description("Sets the default match size for future fluid-round tournaments.")]
async fn fluid_match_size(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[sub_commands("standard")]
#[min_args(1)]
#[delimiters(",")]
#[description("Adjusts the default settings for future tournament that pretain to scoring.")]
async fn scoring(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[min_args(1)]
#[description("")]
async fn standard(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("match-win-points")]
#[min_args(1)]
#[description("")]
async fn match_win_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("match-draw-points")]
#[min_args(1)]
#[description("")]
async fn match_draw_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("match-loss-points")]
#[min_args(1)]
#[description("")]
async fn match_loss_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("game-win-points")]
#[min_args(1)]
#[description("")]
async fn game_win_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("game-draw-points")]
#[min_args(1)]
#[description("")]
async fn game_draw_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("game-loss-points")]
#[min_args(1)]
#[description("")]
async fn game_loss_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("bye-points")]
#[min_args(1)]
#[description("")]
async fn bye_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-byes")]
#[min_args(1)]
#[description("")]
async fn include_byes(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-match-points")]
#[min_args(1)]
#[description("")]
async fn include_match_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-game-points")]
#[min_args(1)]
#[description("")]
async fn include_game_points(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-mwp")]
#[min_args(1)]
#[description("")]
async fn include_mwp(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-gwp")]
#[min_args(1)]
#[description("")]
async fn include_gwp(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-opp-mwp")]
#[min_args(1)]
#[description("")]
async fn include_opp_mwp(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}

#[command]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[aliases("include-opp-gwp")]
#[min_args(1)]
#[description("")]
async fn include_opp_gwp(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    todo!()
}
