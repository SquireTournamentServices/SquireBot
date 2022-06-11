use std::{fs::read_to_string, path::Path};

use serde::{Deserialize, Serialize};

use mtgjson::{
    model::atomics_collection::AtomicCardCollection,
    mtgjson::{atomics::Atomics, meta::Meta},
};

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq)]
struct MetaChecker {
    meta: Meta,
    data: Meta,
}

/// Attempts to build an atomic card collection from an existing atomics file.
/// If that file doesn't exist, a new one is pulled from mtgjson and turned into a collection.
///
/// `None` is returned if there is a file/directory that is not an atomics file at the given path,
/// mtgjson could not be reached, or the collection doesn't need updated.
pub async fn build_collection(meta: &Meta, pth: &Path) -> Option<(Meta, AtomicCardCollection)> {
    let meta_data: MetaChecker = reqwest::get("https://mtgjson.com/api/v5/Meta.json")
        .await
        .ok()?
        .json()
        .await
        .ok()?;
    if meta_data.meta == *meta {
        return None;
    }
    let atomics: Atomics = if pth.exists() && !pth.is_dir() {
        let data = read_to_string(pth.as_os_str()).ok()?;
        serde_json::from_str(&data).ok()?
    } else {
        reqwest::get("https://mtgjson.com/api/v5/AtomicCards.json")
            .await
            .ok()?
            .json()
            .await
            .ok()?
    };
    Some((meta_data.meta, AtomicCardCollection::from(atomics)))
}
