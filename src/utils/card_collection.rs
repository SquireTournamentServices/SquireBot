use std::{fs::read_to_string, path::Path};

use mtgjson::{mtgjson::atomics::Atomics, model::atomics_collection::AtomicCardCollection};


/// Attempts to build an atomic card collection from an existing atomics file.
/// If that file doesn't exist, a new one is pulled from mtgjson and turned into a collection.
///
/// `None` is returned if there is a file/directory that is not an atomics file at the given path
/// or mtgjson could not be reached.
pub async fn build_collection(pth: &Path) -> Option<AtomicCardCollection> {
    if pth.is_dir() {
        return None;
    }
    let atomics: Atomics = if pth.exists() {
        let data = read_to_string(pth.as_os_str()).ok()?;
        serde_json::from_str(&data).ok()?
    } else {
        reqwest::get("https://mtgjson.com/api/v5/AtomicCards.json").await.ok()?.json().await.ok()?
    };
    Some(AtomicCardCollection::from(atomics))
}
