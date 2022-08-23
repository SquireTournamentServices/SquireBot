use uuid::Uuid;

use lazy_static::lazy_static;

use squire_lib::identifiers::AdminId;

pub const DEFAULT_PAIRINGS_CHANNEL_NAME: &str = "match-pairings";
pub const DEFAULT_JUDGE_ROLE_NAME: &str = "Judge";
pub const DEFAULT_TOURN_ADMIN_ROLE_NAME: &str = "Tournament Admin";
pub const DEFAULT_MATCHES_CATEGORY_NAME: &str = "Matches";
pub const MAX_COIN_FLIPS: u64 = 10_000_000;
pub const MAX_KRARK_THUMBS: u64 = 32;
lazy_static!{
    pub static ref SQUIRE_ACCOUNT_ID: AdminId = AdminId::new(Uuid::new_v4());
}
