use serenity::framework::standard::macros::{check, command, group, help, hook};

use super::flip_coins::*;

#[group]
#[commands(flip_coins)]
pub struct MiscCommands;
