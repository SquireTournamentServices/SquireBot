use std::str::FromStr;

use serenity::model::mention::Mention;

pub fn extract_id(s: &str) -> Option<u64> {
    use Mention::*;
    let mention: Mention = Mention::from_str(s).ok()?;
    match mention {
        Channel(id) => Some(id.0),
        Role(id) => Some(id.0),
        User(id) => Some(id.0),
        _ => None,
    }
}
