use squire_core::tournament::{self, Tournament};

use dashmap::DashMap;
use serde::{Deserialize, Serialize};
use serenity::model::id::{ChannelId, GuildId, RoleId};
use serenity::prelude::*;

pub struct SquireTournament {
    tourn: Tournament,
}
