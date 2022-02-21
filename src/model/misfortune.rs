use dashmap::DashMap;
use serenity::{
    model::id::{ChannelId, MessageId, UserId},
    prelude::*,
};
use squire_core::round::RoundId;

use std::collections::{HashMap, HashSet};

pub struct MisfortunePlayerContainer;

impl TypeMapKey for MisfortunePlayerContainer {
    type Value = DashMap<UserId, RoundId>;
}

pub struct MisfortuneContainer;

impl TypeMapKey for MisfortuneContainer {
    type Value = DashMap<RoundId, Misfortune>;
}

pub struct Misfortune {
    players: HashSet<UserId>,
    responses: HashMap<UserId, u64>,
    reply_channel: ChannelId,
    reply_message: MessageId,
}

impl Misfortune {
    pub fn new(
        players: HashSet<UserId>,
        reply_channel: ChannelId,
        reply_message: MessageId,
    ) -> Self {
        let l = players.len();
        Misfortune {
            players,
            responses: HashMap::with_capacity(l),
            reply_channel,
            reply_message,
        }
    }

    pub fn add_response(&mut self, player: UserId, value: u64) -> bool {
        if self.responses.contains_key(&player) || self.players.contains(&player) {
            self.responses.insert(player, value);
        }
        self.responses.len() == self.players.len()
    }

    pub fn get_channel(&self) -> ChannelId {
        self.reply_channel.clone()
    }

    pub fn get_message(&self) -> MessageId {
        self.reply_message.clone()
    }

    pub fn get_responses(&self) -> HashMap<UserId, u64> {
        self.responses.clone()
    }

    pub fn pretty_str(&self) -> String {
        let mut digest = String::with_capacity(self.players.len() * 40);
        for (p, r) in &self.responses {
            digest += &format!("<@{}> answered {}\n", p, r);
        }
        digest
    }
}
