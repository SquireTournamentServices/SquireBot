use dashmap::DashMap;
use serenity::{
    model::id::{MessageId, UserId},
    prelude::*,
};
use squire_core::round::RoundId;

use std::collections::HashMap;

pub struct MisfortuneContainer;

impl TypeMapKey for MisfortuneContainer {
    type Value = DashMap<RoundId, Misfortune>;
}

pub struct Misfortune {
    players: Vec<UserId>,
    responses: HashMap<UserId, u64>,
    reply_message: MessageId,
}

impl Misfortune {
    pub fn new(players: Vec<UserId>, reply_message: MessageId) -> Self {
        let l = players.len();
        Misfortune {
            players,
            responses: HashMap::with_capacity(l),
            reply_message,
        }
    }

    pub fn add_response(&mut self, player: UserId, value: u64) -> bool {
        if self.responses.contains_key(&player) || self.players.contains(&player) {
            self.responses.insert(player, value);
        }
        self.responses.len() == self.players.len()
    }

    pub fn get_message(&self) -> MessageId {
        self.reply_message.clone()
    }

    pub fn get_responses(&self) -> HashMap<UserId, u64> {
        self.responses.clone()
    }
}
