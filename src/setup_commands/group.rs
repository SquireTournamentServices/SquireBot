use serenity::framework::standard::macros::{check, command, group, help, hook};

use super::setup::*;

#[group]
#[commands(setup)]
pub struct SetupCommands;
