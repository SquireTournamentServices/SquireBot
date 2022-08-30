pub mod card_collection;
pub mod embeds;
pub mod error_to_reply;
pub mod extract_id;
pub mod sort_deck;
pub mod spin_lock;
pub mod stringify;
pub mod tourn_resolver;
#[cfg(not(release))]
mod lib_sync;
