use super::confirmation::Confirmation;

use dashmap::DashMap;
use serenity::{
    prelude::TypeMapKey,
    model::id::UserId,
};

pub struct ConfirmationsContainer;

impl  TypeMapKey for ConfirmationsContainer {
    type Value = DashMap<UserId, Box<dyn Confirmation>>;
}
