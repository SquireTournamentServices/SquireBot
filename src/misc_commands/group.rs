use serenity::framework::standard::macros::{check, command, group, help, hook};

use super::{bug::*, confirm::*, docs::*, feature::*, flip_coins::*, misfortune::*, save::*};

#[group]
#[commands(flip_coins, docs, misfortune, save, bug, feature, yes, no)]
pub struct MiscCommands;
