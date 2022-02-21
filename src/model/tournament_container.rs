use squire_core::tournament_registry::TournamentRegistry;

use serenity::prelude::*;

use std::sync::Arc;

pub struct TournamentContainer;

impl TypeMapKey for TournamentContainer {
    type Value = TournamentRegistry;
}
