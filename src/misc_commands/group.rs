use serenity::framework::standard::macros::{check, command, group, help, hook};

use super::{bug::*, confirm::*, dump::*, feature::*, flip_coins::*, misfortune::*};

#[group]
#[commands(flip_coins, misfortune, dump, bug, feature, yes, no)]
pub struct MiscCommands;
