use serenity::framework::standard::macros::{check, command, group, help, hook};

use super::{docs::*, bug::*, confirm::*, save::*, feature::*, flip_coins::*, misfortune::*};

#[group]
#[commands(flip_coins, docs, misfortune, save, bug, feature, yes, no)]
pub struct MiscCommands;
