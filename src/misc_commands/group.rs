use serenity::framework::standard::macros::group;

use super::{bug::*, confirm::*, docs::*, feature::*, flip_coins::*, save::*};

#[group]
#[commands(flip_coins, docs, save, bug, feature, yes, no)]
pub struct MiscCommands;
