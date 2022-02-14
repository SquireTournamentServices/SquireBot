use serenity::framework::standard::macros::{check, command, group, help, hook};

use super::tournament::*;

#[group]
#[commands(tournament)]
pub struct TournamentCommands;
