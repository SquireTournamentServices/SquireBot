use std::{str::FromStr, sync::Arc, time::Duration};

use serenity::{
    framework::standard::{macros::command, Args, CommandError, CommandResult},
    model::{
        channel::{Channel, ChannelType},
        mention::Mention,
        prelude::Message,
    },
    prelude::Context,
};

use squire_lib::{
    identifiers::{AdminId, PlayerId, RoundIdentifier},
    operations::{AdminOp, JudgeOp, TournOp},
};

use crate::{
    logging::LogAction,
    model::{
        consts::SQUIRE_ACCOUNT_ID,
        containers::{
            CardCollectionContainer, GuildTournRegistryMapContainer, LogActionSenderContainer,
        },
        guilds::GuildTournamentAction::{self, *},
    },
    utils::{
        default_response::subcommand_default, id_resolver::{user_id_resolver, parse_round_ident}, spin_lock::spin_mut,
    },
};

// Require player info
#[command("add-deck")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<player name/mention>, <deck name>, <deck list/url>, [tournament name]")]
#[example("'SomePlayer', 'SomeDeck', https://moxfield.com/decks/qwertyuiop/")]
#[example("@SomePlayer, 'SomeDeck', 'https://moxfield.com/decks/qwertyuiop/'")]
#[description("Adds a deck on behalf of a player.")]
async fn add_deck(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let raw_user_id = match get_raw_user_id(msg, ctx, &mut args).await? {
        Some(s) => s,
        None => {
            return Ok(());
        }
    };
    let deck_name = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please include a deck name.").await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let raw_deck = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please include a deck.").await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let tourn_name = args.rest().trim().to_string();
    let data = ctx.data.read().await;
    let card_coll = data.get::<CardCollectionContainer>().unwrap().read().await;
    let logger = data.get::<LogActionSenderContainer>().unwrap();
    let _ = logger.send((msg.id, LogAction::CouldPanic("getting card collection")));
    match card_coll.import_deck(raw_deck.clone()).await {
        Some(deck) => {
            admin_command(ctx, msg, raw_user_id, tourn_name, move |admin, p| {
                Operation(TournOp::JudgeOp(
                    admin.into(),
                    JudgeOp::AdminAddDeck(p.into(), deck_name, deck),
                ))
            })
            .await
        }
        None => {
            msg.reply(&ctx.http, "Unable to create a deck from this.")
                .await?;
            Ok(())
        }
    }
}

#[command("confirm-result")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<player name/mention>, [tournament name]")]
#[example("'SomePlayer'")]
#[example("@SomePlayer")]
#[description("Confirms a match result on behalf of a player.")]
async fn confirm_result(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let raw_user_id = match get_raw_user_id(msg, ctx, &mut args).await? {
        Some(s) => s,
        None => {
            return Ok(());
        }
    };
    let r_ident = match args.single::<String>().ok().map(|s| parse_round_ident(s.as_str())).flatten() {
        Some(id) => id,
        None => {
            msg.reply(&ctx.http, "Please include the match number.")
                .await?;
            return Ok(());
        }
    };
    let tourn_name = args.rest().trim().to_string();
    admin_command(ctx, msg, raw_user_id, tourn_name, move |_, p| {
        AdminConfirmResult(r_ident, p.into())
    })
    .await
}

#[command("open-matches")]
#[only_in(guild)]
#[allowed_roles("Judge", "Tournament Admin")]
#[usage("[tournament name]")]
#[description("Pulls up a list of open matches")]
async fn open_matches(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| OpenMatches).await
}

#[command("confirm-all")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("[tournament name]")]
#[description("Confirms all active matches.")]
async fn confirm_all(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| ConfirmAll).await
}

#[command("decklist")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<player name/mention>, <deck name>, [tournament name]")]
#[example("'SomePlayer', SomeDeck")]
#[example("@SomePlayer, 'SomeDeck'")]
#[description("Prints out the decklist of a player.")]
async fn decklist(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let raw_user_id = match get_raw_user_id(msg, ctx, &mut args).await? {
        Some(s) => s,
        None => {
            return Ok(());
        }
    };
    let deck_name = match args.single_quoted::<String>() {
        Ok(s) if !s.is_empty() => s,
        _ => {
            msg.reply(&ctx.http, "Please include a deck name.").await?;
            return Ok(());
        }
    };
    if deck_name.is_empty() {
        msg.reply(&ctx.http, "Please include the name of the deck.")
            .await?;
        return Ok(());
    }
    let tourn_name = args.rest().trim().to_string();
    admin_command(ctx, msg, raw_user_id, tourn_name, move |_, p| {
        ViewDecklist(p.into(), deck_name)
    })
    .await
}

#[command("drop")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("<player name/mention>, [tournament name]")]
#[example("'SomePlayer'")]
#[example("@SomePlayer")]
#[description("Drops a player from the tournament.")]
async fn drop(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let raw_user_id = match get_raw_user_id(msg, ctx, &mut args).await? {
        Some(s) => s,
        None => {
            return Ok(());
        }
    };
    let tourn_name = args.rest().trim().to_string();
    admin_command(ctx, msg, raw_user_id, tourn_name, move |_, p| {
        DropPlayer(p.into())
    })
    .await
}

#[command("give-bye")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("<player name/mention>, [tournament name]")]
#[example("'SomePlayer'")]
#[example("@SomePlayer")]
#[description("Gives a player a bye.")]
async fn give_bye(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let raw_user_id = match get_raw_user_id(msg, ctx, &mut args).await? {
        Some(s) => s,
        None => {
            return Ok(());
        }
    };
    let tourn_name = args.rest().trim().to_string();
    admin_command(ctx, msg, raw_user_id, tourn_name, move |_, p| {
        GiveBye(p.into())
    })
    .await
}

#[command("re-register")]
#[only_in(guild)]
#[sub_commands("guest")]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<player name/mention>, [tournament name]")]
#[example("'SomePlayer'")]
#[example("@SomePlayer")]
#[description("Re-registers a player on their behalf.")]
async fn re_register(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let raw_user_id = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(
                &ctx.http,
                "Please include a player, either by name or mention.",
            )
            .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let gld = msg.guild(&ctx.cache).unwrap();
    let user_id = match user_id_resolver(&raw_user_id, &gld).await {
        Some(id) => id,
        None => {
            msg.reply(&ctx.http, "That person could not be found.")
                .await?;
            return Ok(());
        }
    };
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| {
        AdminReRegisterPlayer(user_id)
    })
    .await
}

#[command("register")]
#[only_in(guild)]
#[sub_commands("guest")]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<player name/mention>, [tournament name]")]
#[example("'SomePlayer'")]
#[example("@SomePlayer")]
#[description("Registers a player on their behalf.")]
async fn register(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let raw_user_id = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(
                &ctx.http,
                "Please include a player, either by name or mention.",
            )
            .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let gld = msg.guild(&ctx.cache).unwrap();
    let user_id = match user_id_resolver(&raw_user_id, &gld).await {
        Some(id) => id,
        None => {
            msg.reply(&ctx.http, "That person could not be found.")
                .await?;
            return Ok(());
        }
    };
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| AdminRegisterPlayer(user_id)).await
}

#[command("guest")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<player name>, [tournament name]")]
#[example("'SomePlayer'")]
#[description("Registers a player that isn't on Discord.")]
async fn guest(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let user_name = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please include the player's name.")
                .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| RegisterGuest(user_name)).await
}

#[command("match-result")]
#[only_in(guild)]
#[sub_commands(draws)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<player name/mention>, <match #>, <# of wins>, [tournament name]")]
#[example("'SomePlayer', 10, 1")]
#[example("@SomePlayer, 10")]
#[description("Records the result of a match.")]
async fn match_result(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::rounds::RoundResult::Wins;
    let raw_user_id = match get_raw_user_id(msg, ctx, &mut args).await? {
        Some(s) => s,
        None => {
            return Ok(());
        }
    };
    let r_ident = match args.single::<String>().ok().map(|s| parse_round_ident(s.as_str())).flatten() {
        Some(id) => id,
        None => {
            msg.reply(
                &ctx.http,
                "The second argument must be a proper match or table number.",
            )
            .await?;
            return Ok(());
        }
    };
    let wins = match args.single::<u32>() {
        Err(_) => {
            msg.reply(
                &ctx.http,
                "Please include the number of time the player won.",
            )
            .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let tourn_name = args.rest().trim().to_string();
    admin_command(ctx, msg, raw_user_id, tourn_name, move |_, p| {
        AdminRecordResult(r_ident, Wins(p, wins))
    })
    .await
}

#[command("draws")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<player name/mention>, <match #>, <# of draws>, [tournament name]")]
#[example("'SomePlayer', 10, 1")]
#[example("@SomePlayer, 10")]
#[description("Records the result of a match.")]
async fn draws(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    use squire_lib::rounds::RoundResult::Draw;
    let raw_user_id = match get_raw_user_id(msg, ctx, &mut args).await? {
        Some(s) => s,
        None => {
            return Ok(());
        }
    };
    let r_ident = match args.single::<u64>() {
        Ok(n) => RoundIdentifier::Number(n),
        Err(_) => {
            msg.reply(
                &ctx.http,
                "The second argument must be a proper match number.",
            )
            .await?;
            return Ok(());
        }
    };
    let draws = match args.single::<u32>() {
        Err(_) => {
            msg.reply(
                &ctx.http,
                "Please include the number of time the player won.",
            )
            .await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let tourn_name = args.rest().trim().to_string();
    admin_command(ctx, msg, raw_user_id, tourn_name, move |_, _| {
        AdminRecordResult(r_ident, Draw(draws))
    })
    .await
}

#[command("profile")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<player name/mention>, [tournament name]")]
#[example("'SomePlayer'")]
#[example("@SomePlayer")]
#[description("Prints out the profile of a player.")]
async fn profile(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let raw_user_id = match get_raw_user_id(msg, ctx, &mut args).await? {
        Some(s) => s,
        None => {
            return Ok(());
        }
    };
    let tourn_name = args.rest().trim().to_string();
    admin_command(ctx, msg, raw_user_id, tourn_name, move |_, p_id| {
        ViewPlayerProfile(p_id.into())
    })
    .await
}

#[command("remove-deck")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<player name/mention>, <deck name>, [tournament name]")]
#[example("'SomePlayer', https://moxfield.com/decks/qwertyuiop/")]
#[example("@SomePlayer, https://moxfield.com/decks/qwertyuiop/")]
#[description("Removes a deck on behave of a player.")]
async fn remove_deck(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let raw_user_id = match get_raw_user_id(msg, ctx, &mut args).await? {
        Some(s) => s,
        None => {
            return Ok(());
        }
    };
    let deck_name = match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(&ctx.http, "Please include a deck name.").await?;
            return Ok(());
        }
        Ok(s) => s,
    };
    let tourn_name = args.rest().trim().to_string();
    admin_command(ctx, msg, raw_user_id, tourn_name, move |admin, p_id| {
        Operation(TournOp::JudgeOp(
            admin.into(),
            JudgeOp::AdminRemoveDeck(p_id.into(), deck_name),
        ))
    })
    .await
}

// Don't require player info
#[command("cut")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("<top N>, [tournament name]")]
#[example("16")]
#[description("Drops all but the top N players.")]
async fn cut(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let len = match args.single_quoted::<usize>() {
        Ok(n) => n,
        Err(_) => {
            msg.reply(&ctx.http, "Please include the number you wish to cut to.")
                .await?;
            return Ok(());
        }
    };
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| Cut(msg.author.id, len)).await
}

#[command("end")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("[tournament name]")]
#[example("end")]
#[description("Ends a tournament.")]
async fn end(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| End(msg.author.id)).await
}

#[command("cancel")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("[tournament name]")]
#[example("cancel")]
#[description("Cancels a tournament.")]
async fn cancel(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| Cancel(msg.author.id)).await
}

#[command("freeze")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("[tournament name]")]
#[example("freeze")]
#[description("Pauses a tournament.")]
async fn freeze(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |admin| {
        Operation(TournOp::AdminOp(admin, AdminOp::Freeze))
    })
    .await
}

#[command("thaw")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("[tournament name]")]
#[example("thaw")]
#[description("Resumes a frozen a tournament.")]
async fn thaw(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |admin| {
        Operation(TournOp::AdminOp(admin, AdminOp::Thaw))
    })
    .await
}

#[command("match-status")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<match #>, [tournament name]")]
#[example("10")]
#[description("Prints an embed of the status of a match.")]
async fn match_status(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let r_ident = match args.single::<String>().ok().map(|s| parse_round_ident(s.as_str())).flatten() {
        Some(id) => id,
        None => {
            msg.reply(
                &ctx.http,
                "The first argument must be a proper match number.",
            )
            .await?;
            return Ok(());
        }
    };
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| ViewMatchStatus(r_ident)).await
}

#[command("pair")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("[tournament name]")]
#[description("Pairs the next round of matches.")]
async fn pair(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| PairRound(msg.author.id)).await
}

#[command("view-players")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("[tournament name]")]
#[description("Prints out a list of all players.")]
async fn view_players(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| {
        GuildTournamentAction::ViewAllPlayers
    })
    .await
}

#[command("prune")]
#[only_in(guild)]
#[sub_commands(players, decks)]
#[allowed_roles("Tournament Admin")]
#[usage("<option>")]
#[description(
    "Removes players that aren't fully registered and decks from players that have them in excess."
)]
async fn prune(ctx: &Context, msg: &Message, _: Args) -> CommandResult {
    subcommand_default(ctx, msg, "tournament admin prune").await
}

#[command("players")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("[tournament name]")]
#[description("Removes players that aren't fully registered.")]
async fn players(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| PrunePlayers(msg.author.id)).await
}

#[command("decks")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("[tournament name]")]
#[description("Removes decks from players that have them in excess.")]
async fn decks(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| PruneDecks(msg.author.id)).await
}

#[command("raw-standings")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<top N>, [tournament name]")]
#[example("25")]
#[description("Delivers a txt file with simplified standings.")]
async fn raw_standings(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let count = match args.single_quoted::<String>().as_ref().map(|s| s.as_str()) {
        Ok("all" | "All" | "a" | "A") => usize::max_value(),
        res => match res.ok().and_then(|s| s.parse::<usize>().ok()) {
            Some(n) => n,
            None => {
                msg.reply(&ctx.http, r#"Please specify a max count or the word "all""#)
                    .await?;
                return Ok(());
            }
        },
    };
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| GetRawStandings(count)).await
}

#[command("export-tournament")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[description("Exports a tournament as a JSON file to be used in desktop app.")]
async fn export_tournament(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| ExportTournament).await
}

#[command("registration")]
#[only_in(guild)]
#[aliases("reg")]
#[allowed_roles("Tournament Admin")]
#[usage("<open/closed>, [tournament name]")]
#[description("Changes the registeration status of the tournament.")]
async fn registration(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let reg_status = match args.single_quoted::<String>().as_ref().map(|s| s.as_str()) {
        Ok("open") | Ok("Open") => true,
        Ok("closed") | Ok("Closed") => false,
        _ => {
            msg.reply(&ctx.http, "Please specify 'open' or 'closed'.")
                .await?;
            return Ok(());
        }
    };
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |admin| {
        Operation(TournOp::AdminOp(admin, AdminOp::UpdateReg(reg_status)))
    })
    .await
}
#[command("remove-match")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("<match #>, [tournament name]")]
#[example("10")]
#[description("Adds a match from the tournament.")]
async fn remove_match(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let r_ident = match args.single::<String>().ok().map(|s| parse_round_ident(s.as_str())).flatten() {
        Some(id) => id,
        None => {
            msg.reply(
                &ctx.http,
                "The second argument must be a proper match number.",
            )
            .await?;
            return Ok(());
        }
    };
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| RemoveMatch(r_ident)).await
}

#[command("standings")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("[tournament name]")]
#[description("Creates an auto-updating standings message.")]
async fn standings(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
        Ok(c_id) => match ctx.cache.channel(&c_id) {
            Some(channel) => match channel {
                Channel::Guild(c) if c.kind == ChannelType::Text => {
                    let tourn_name = args.rest().trim().to_string();
                    admin_command_without_player(ctx, msg, tourn_name, move |_| {
                        CreateStandings(Arc::new(c))
                    })
                    .await?;
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

#[command("start")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("[tournament name]")]
#[description("Starts a tournament.")]
async fn start(ctx: &Context, msg: &Message, args: Args) -> CommandResult {
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |admin| {
        Operation(TournOp::AdminOp(admin, AdminOp::Start))
    })
    .await
}

#[command("status")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("[tournament name]")]
#[description("Creates an auto-updating status containing all information about the tournament.")]
async fn status(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
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
        Ok(c_id) => match ctx.cache.channel(&c_id) {
            Some(channel) => match channel {
                Channel::Guild(c) if c.kind == ChannelType::Text => {
                    let tourn_name = args.rest().trim().to_string();
                    admin_command_without_player(ctx, msg, tourn_name, move |_| {
                        CreateTournamentStatus(Arc::new(c))
                    })
                    .await?;
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
#[command("time-extension")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<match #>, <# of minutes>, [tournament name]")]
#[example("10, 5")]
#[description("Give a match a time extenstion.")]
async fn time_extension(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let r_ident = match args.single::<String>().ok().map(|s| parse_round_ident(s.as_str())).flatten() {
        Some(id) => id,
        None => {
            msg.reply(
                &ctx.http,
                "The second argument must be a proper match number.",
            )
            .await?;
            return Ok(());
        }
    };
    let ext = match args.single_quoted::<u64>() {
        Ok(t) => Duration::from_secs(t * 60),
        Err(_) => {
            msg.reply(
                &ctx.http,
                "Specify, in minutes, how long the extenstion is.",
            )
            .await?;
            return Ok(());
        }
    };
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| {
        TimeExtension(r_ident, ext)
    })
    .await
}

#[command("create-match")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("<player name/mention>, ..., [tournament name]")]
#[example("'PlayerA', 'PlayerB'")]
#[example("@PlayerA, @PlayerB")]
#[description("Adds a match consisting of the specified players.")]
async fn create_match(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let raw_players: Vec<String> = args
        .iter::<String>()
        .quoted()
        .filter_map(|a| a.ok())
        .collect();
    let tourn_name: String = raw_players.last().cloned().unwrap_or_default();
    admin_command_without_player(ctx, msg, tourn_name, move |_| CreateMatch(raw_players)).await
}

#[command("deck-check")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin", "Judge")]
#[usage("<match number>, [tournament name]")]
#[example("10")]
#[description("Prints out all decks from all players in a match.")]
async fn deck_check(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let r_ident = match args.single::<String>().ok().map(|s| parse_round_ident(s.as_str())).flatten() {
        Some(id) => id,
        None => {
            msg.reply(
                &ctx.http,
                "The first argument must be a proper match number.",
            )
            .await?;
            return Ok(());
        }
    };
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| DeckCheck(r_ident)).await
}

#[command("deck-dump")]
#[only_in(guild)]
#[allowed_roles("Tournament Admin")]
#[usage("<count>, [tournament name]")]
#[example("10")]
#[description("Prints out all decks from all top N players.")]
async fn deck_dump(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let count = match args.single::<usize>() {
        Ok(n) => n,
        Err(_) => {
            msg.reply(
                &ctx.http,
                "The first argument must be a proper whole number.",
            )
            .await?;
            return Ok(());
        }
    };
    let tourn_name = args.rest().trim().to_string();
    admin_command_without_player(ctx, msg, tourn_name, move |_| DeckDump(count)).await
}

async fn get_raw_user_id(
    msg: &Message,
    ctx: &Context,
    args: &mut Args,
) -> Result<Option<String>, CommandError> {
    match args.single_quoted::<String>() {
        Err(_) => {
            msg.reply(
                &ctx.http,
                "Please include a player, either by name or mention.",
            )
            .await?;
            Ok(None)
        }
        Ok(s) => Ok(Some(s)),
    }
}

async fn admin_command<'a, F>(
    ctx: &Context,
    msg: &Message,
    raw_user_id: String,
    tourn_name: String,
    f: F,
) -> CommandResult
where
    F: FnOnce(AdminId, PlayerId) -> GuildTournamentAction,
{
    let data = ctx.data.read().await;
    let tourn_regs = data
        .get::<GuildTournRegistryMapContainer>()
        .unwrap()
        .read()
        .await;
    let gld = msg.guild(&ctx.cache).unwrap();
    let mut reg = spin_mut(&tourn_regs, &gld.id).await.unwrap();
    let tourn = match reg.get_tourn_mut(&tourn_name) {
        Some(t) => t,
        None => {
            msg.reply(&ctx.http, "That tournament could not be found.")
                .await?;
            return Ok(());
        }
    };
    let plyr_id = match user_id_resolver(&raw_user_id, &gld).await {
        Some(user_id) => match tourn.players.get_right(&user_id) {
            Some(id) => *id,
            None => {
                msg.reply(
                    &ctx.http,
                    "That player is not registered for the tournament.",
                )
                .await?;
                return Ok(());
            }
        },
        None => match tourn.guests.get_right(&raw_user_id) {
            Some(id) => *id,
            None => {
                msg.reply(
                        &ctx.http,
                        "That guest is not registered for the tournament. You may have mistyped their name.",
                    )
                    .await?;
                return Ok(());
            }
        },
    };
    let content = tourn
        .take_action(ctx, f(*SQUIRE_ACCOUNT_ID, plyr_id))
        .await?;
    content.message_reply(ctx, msg).await
}
async fn admin_command_without_player<'a, F>(
    ctx: &Context,
    msg: &Message,
    tourn_name: String,
    f: F,
) -> CommandResult
where
    F: FnOnce(AdminId) -> GuildTournamentAction,
{
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
    let content = tourn.take_action(ctx, f(*SQUIRE_ACCOUNT_ID)).await?;
    content.message_reply(ctx, msg).await
}
