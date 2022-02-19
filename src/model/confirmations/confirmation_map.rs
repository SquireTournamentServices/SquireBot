use super::confirmation::Confirmation;

use dashmap::DashMap;
use serenity::{model::id::UserId, prelude::TypeMapKey};

pub struct ConfirmationsContainer;

impl TypeMapKey for ConfirmationsContainer {
    type Value = DashMap<UserId, Box<dyn Confirmation>>;
}
