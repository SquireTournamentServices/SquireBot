use serenity::framework::standard::macros::{check, command, group, help, hook};

use super::flip_coins::*;
use super::confirm::*;

#[group]
#[commands(flip_coins, yes, no)]
pub struct MiscCommands;
