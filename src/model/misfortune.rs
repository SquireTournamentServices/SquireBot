use std::{
    collections::{HashMap, HashSet},
    fmt::Write,
};

use dashmap::DashMap;
use serenity::{
    model::id::{ChannelId, MessageId, UserId},
    prelude::*,
};

use squire_lib::round::RoundId;

pub struct Misfortune {
    pub players: HashSet<UserId>,
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
        self.reply_channel
    }

    pub fn get_message(&self) -> MessageId {
        self.reply_message
    }

    pub fn get_responses(&self) -> HashMap<UserId, u64> {
        self.responses.clone()
    }

    pub fn pretty_str(&self) -> String {
        let mut digest = String::with_capacity(self.players.len() * 40);
        for (p, r) in &self.responses {
            let _ = writeln!(digest, "<@{p}> answered {r}");
        }
        digest
    }
}
