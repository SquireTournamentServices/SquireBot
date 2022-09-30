#![allow(unused, missing_docs)]

use std::collections::HashMap;

use chrono::{DateTime, Duration, Utc};
use serenity::model::id::MessageId;
use tokio::sync::mpsc::UnboundedReceiver;

// Figure out the maximum number of logs needed for a command
pub const MAX_LOG_ACTION: usize = 10;
pub const DEFAULT_TIME_TO_LIVE_SECS: u64 = 10;

pub enum LogAction {
    Start(String, DateTime<Utc>),
    CouldFail(&'static str),
    CouldPanic(&'static str),
    TakingLock(&'static str),
    End(bool, DateTime<Utc>),
}

pub struct LogTracker {
    incoming: UnboundedReceiver<(MessageId, LogAction)>,
    active: HashMap<MessageId, Vec<LogAction>>,
    timers: HashMap<MessageId, DateTime<Utc>>,
    pub time_to_live: Duration,
}

impl LogTracker {
    pub fn new(incoming: UnboundedReceiver<(MessageId, LogAction)>) -> Self {
        Self {
            incoming,
            active: HashMap::with_capacity(100),
            timers: HashMap::with_capacity(100),
            time_to_live: Duration::from_std(std::time::Duration::from_secs(
                DEFAULT_TIME_TO_LIVE_SECS,
            ))
            .unwrap(),
        }
    }

    pub fn process(&mut self) {
        let mut closed = Vec::new();
        while let Ok((msg, action)) = self.incoming.try_recv() {
            match &action {
                LogAction::Start(..) => {
                    let mut actions = Vec::with_capacity(MAX_LOG_ACTION);
                    actions.push(action);
                    self.timers.insert(msg.clone(), Utc::now());
                    self.active.insert(msg, actions);
                }
                LogAction::End(..) => {
                    self.timers.remove(&msg);
                    if let Some(mut actions) = self.active.remove(&msg) {
                        actions.push(action);
                        closed.push((msg, actions));
                    } else {
                        // TODO: A command took longer than `self.time_to_live`. We should record
                        // this!
                    }
                }
                _ => {
                    self.active
                        .get_mut(&msg)
                        .map(|actions| actions.push(action));
                }
            }
        }
        // TODO: Log the successful commands somewhere
        // Use this data to calculate things like number of locks taken and total response time.
        // This would also be interesting to see a profile based on command type
        let now = Utc::now();
        let mut timed_out = Vec::new();
        for (msg, timer) in self.timers.iter() {
            if (now - *timer) > self.time_to_live {
                timed_out.push(msg);
            }
        }
        for msg in timed_out {
            self.timers.remove(&msg);
            let actions = self.active.remove(&msg).unwrap();
            // TODO: Log the paniced commands with the "stack trace"
            // TODO: Spawn a tokio task to send an embed of this error to the dev server (if
            // applicable)
        }
    }
}

fn panic_report_fields(
    msg_id: MessageId,
    log: Vec<LogAction>,
) -> Vec<(String, Vec<String>, &'static str, bool)> {
    todo!()
}
