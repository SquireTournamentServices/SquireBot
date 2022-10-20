#![allow(unused, missing_docs)]

use std::{collections::HashMap, fmt::Display};

use chrono::{DateTime, Duration, Utc};
use itertools::Itertools;
use serenity::{
    client::Context,
    http::CacheHttp,
    model::{channel::GuildChannel, id::MessageId},
};
use tokio::sync::mpsc::UnboundedReceiver;

use crate::utils::embeds::safe_embeds;

// Figure out the maximum number of logs needed for a command
pub const MAX_LOG_ACTION: usize = 10;
pub const DEFAULT_TIME_TO_LIVE_SECS: u64 = 10;

pub enum LogAction {
    Start(String, DateTime<Utc>),
    Info(&'static str),
    CouldFail(&'static str),
    CouldPanic(&'static str),
    TakingLock(&'static str),
    End(bool, DateTime<Utc>),
}

pub struct CommandLog {
    pub start: DateTime<Utc>,
    pub log: Vec<LogAction>,
}

pub struct LogTracker {
    incoming: UnboundedReceiver<(MessageId, LogAction)>,
    active: HashMap<MessageId, CommandLog>,
    successes: HashMap<MessageId, Duration>,
    delays: HashMap<MessageId, Duration>,
    failures: HashMap<MessageId, Duration>,
    panics: HashMap<MessageId, CommandLog>,
    last_report: DateTime<Utc>,
    pub telemetry_channel: GuildChannel,
    pub issue_channel: GuildChannel,
    pub time_to_live: Duration,
}

impl LogTracker {
    pub fn new(
        telemetry_channel: GuildChannel,
        issue_channel: GuildChannel,
        incoming: UnboundedReceiver<(MessageId, LogAction)>,
    ) -> Self {
        Self {
            incoming,
            telemetry_channel,
            issue_channel,
            last_report: Utc::now(),
            successes: HashMap::new(),
            delays: HashMap::new(),
            failures: HashMap::new(),
            panics: HashMap::new(),
            active: HashMap::with_capacity(100),
            time_to_live: Duration::from_std(std::time::Duration::from_secs(
                DEFAULT_TIME_TO_LIVE_SECS,
            ))
            .unwrap(),
        }
    }

    pub fn process(&mut self) -> Vec<MessageId> {
        while let Ok((msg, action)) = self.incoming.try_recv() {
            match &action {
                LogAction::Start(..) => {
                    let mut log = CommandLog::new();
                    log.add_action(action);
                    self.active.insert(msg, log);
                }
                LogAction::End(success, now) => {
                    match self.active.remove(&msg) {
                        Some(log) if *success => {
                            self.successes.insert(msg, *now - log.start);
                        }
                        Some(log) => {
                            self.failures.insert(msg, *now - log.start);
                        }
                        None => {
                            // This should only be None if the telemetry report goes out between
                            // the this process call and the last. In this case, we just ignore it.
                            if let Some(log) = self.panics.remove(&msg) {
                                self.delays.insert(msg, *now - log.start);
                            }
                        }
                    }
                }
                _ => {
                    // This was removed because it was assumed to be a panic.
                    if let Some(actions) = self.active.get_mut(&msg) {
                        actions.add_action(action);
                    }
                }
            }
        }

        let now = Utc::now();
        let mut timed_out = Vec::new();
        for (msg, log) in self.active.iter() {
            if (now - log.start) > self.time_to_live {
                timed_out.push(*msg);
            }
        }

        // Timed out requests are assumed to have panicked.
        for msg in timed_out.iter() {
            let log = self.active.remove(msg).unwrap();
            self.panics.insert(*msg, log);
        }
        timed_out
    }

    pub async fn report_issues(&self, cache: impl CacheHttp, issues: Vec<MessageId>) {
        for msg in issues {
            if let Some(log) = self.panics.get(&msg) {
                let _ = self
                    .issue_channel
                    .send_message(&cache, |m| {
                        m.add_embeds(safe_embeds(
                            "Panic Detected:".into(),
                            panic_report_fields(msg, log),
                        ))
                    })
                    .await;
            }
        }
    }

    pub async fn report_telemetry(&mut self, cache: impl CacheHttp) {
        let mut fields: Vec<(String, Vec<String>, &str, bool)> = Vec::with_capacity(4);
        let total =
            self.successes.len() + self.delays.len() + self.failures.len() + self.panics.len();

        // Overview calculations
        self.successes.clear();
        let mut overview = vec![
            format!("Total requests: {total}"),
            format!(
                "Percent success: {:.2}%",
                (self.successes.len() as f64) / (total as f64) * 100.0
            ),
        ];
        fields.push(("Overview".into(), overview, "\n", true));

        // Delays calculations
        let length = self.delays.len();
        let p_stats = calculate_p_stats(self.delays.drain().map(|(_, dur)| dur).collect());
        let mut delays = vec![
            format!(
                "Requests that took {} seconds to process: {length}",
                self.time_to_live.num_seconds()
            ),
            format!("P50: {} msec", p_stats.0),
            format!("P75: {} msec", p_stats.1),
            format!("P90: {} msec", p_stats.2),
            format!("P99: {} msec", p_stats.3),
            format!("P100: {} msec", p_stats.4),
        ];
        fields.push(("Delays:".into(), delays, "\n", true));

        // Failures calculations
        let length = self.failures.len();
        let p_stats = calculate_p_stats(self.failures.drain().map(|(_, dur)| dur).collect());
        let mut failures = vec![
            format!("Requests that returned an error: {length}"),
            format!("P50: {} msec", p_stats.0),
            format!("P75: {} msec", p_stats.1),
            format!("P90: {} msec", p_stats.2),
            format!("P99: {} msec", p_stats.3),
            format!("P100: {} msec", p_stats.4),
        ];
        fields.push(("Failures:".into(), failures, "\n", true));

        // Panics calculations
        let length = self.panics.len();
        self.panics.clear();
        let mut panics = vec![format!("Requests that panicked: {length}")];
        fields.push(("Panics:".into(), panics, "\n", true));
        let _ = self
            .telemetry_channel
            .send_message(cache, |m| {
                m.add_embeds(safe_embeds(
                    "Today's SquireBot Telemetry Report:".into(),
                    fields,
                ))
            })
            .await;
    }
}

fn panic_report_fields(
    msg_id: MessageId,
    log: &CommandLog,
) -> Vec<(String, Vec<String>, &'static str, bool)> {
    let basics = if let Some(LogAction::Start(name, time)) = log.log.first() {
        vec![
            format!("Command: `{name}`"),
            format!("Time of Panic: {time}"),
        ]
    } else {
        vec![]
    };
    let trace = vec![
        "```".into(),
        log.log.iter().map(|action| action.to_string()).join("\n"),
        "```".into(),
    ];
    vec![
        ("Basic Info:".into(), basics, "\n", false),
        ("Event Log:".into(), trace, "\n", false),
    ]
}

fn calculate_p_stats(mut vals: Vec<Duration>) -> (i64, i64, i64, i64, i64) {
    if vals.is_empty() {
        return (0, 0, 0, 0, 0);
    }
    vals.sort();
    let p_50_index = vals.len() / 2;
    let p_75_index = 3 * vals.len() / 4;
    let p_90_index = 9 * vals.len() / 10;
    let p_99_index = 99 * vals.len() / 100;
    (
        vals[p_50_index].num_milliseconds(),
        vals[p_75_index].num_milliseconds(),
        vals[p_90_index].num_milliseconds(),
        vals[p_99_index].num_milliseconds(),
        vals.last().unwrap().num_milliseconds(),
    )
}

impl CommandLog {
    fn new() -> Self {
        Self {
            start: Utc::now(),
            log: Vec::with_capacity(MAX_LOG_ACTION),
        }
    }

    fn add_action(&mut self, action: LogAction) {
        self.log.push(action);
    }
}

impl Default for CommandLog {
    fn default() -> Self {
        Self::new()
    }
}

impl Display for LogAction {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        use LogAction::*;
        match self {
            Start(name, time) => {
                write!(f, "Starting `{name}` at {time}")
            }
            Info(info) => {
                write!(f, "Info `{info}`")
            }
            CouldFail(action) => {
                write!(f, "Could fail at {action}")
            }
            CouldPanic(action) => {
                write!(f, "Could panic at {action}")
            }
            TakingLock(action) => {
                write!(f, "Taking lock at {action}")
            }
            End(success, time) => {
                write!(
                    f,
                    "Ended {}successfully at {time}",
                    if *success { "" } else { "un" }
                )
            }
        }
    }
}
