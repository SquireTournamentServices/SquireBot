use serenity::framework::standard::macros::{check, command, group, help, hook};

use super::confirm::*;
use super::flip_coins::*;
use super::misfortune::*;

#[group]
#[commands(flip_coins, misfortune, yes, no)]
pub struct MiscCommands;
