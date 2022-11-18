use std::{hash::Hash, time::Duration};

use dashmap::{
    mapref::one::{Ref, RefMut},
    try_result::TryResult,
    DashMap,
};

#[allow(dead_code)]
pub async fn spin<'a, A: Eq + Hash, B>(
    map: &'a DashMap<A, B>,
    key: &'a A,
) -> Option<Ref<'a, A, B>> {
    dur_spin(map, key, Duration::from_millis(1)).await
}

pub async fn spin_mut<'a, A: Eq + Hash, B>(
    map: &'a DashMap<A, B>,
    key: &'a A,
) -> Option<RefMut<'a, A, B>> {
    dur_spin_mut(map, key, Duration::from_millis(1)).await
}

#[allow(dead_code)]
pub async fn dur_spin<'a, A: Eq + Hash, B>(
    map: &'a DashMap<A, B>,
    key: &'a A,
    dur: Duration,
) -> Option<Ref<'a, A, B>> {
    let mut sleep = tokio::time::interval(dur);
    sleep.tick().await;
    loop {
        match map.try_get(key) {
            TryResult::Absent => {
                return None;
            }
            TryResult::Present(val) => {
                return Some(val);
            }
            TryResult::Locked => {
                sleep.tick().await;
            }
        }
    }
}

pub async fn dur_spin_mut<'a, A: Eq + Hash, B>(
    map: &'a DashMap<A, B>,
    key: &'a A,
    dur: Duration,
) -> Option<RefMut<'a, A, B>> {
    let mut sleep = tokio::time::interval(dur);
    sleep.tick().await;
    loop {
        match map.try_get_mut(key) {
            TryResult::Absent => {
                return None;
            }
            TryResult::Present(val) => {
                return Some(val);
            }
            TryResult::Locked => {
                sleep.tick().await;
            }
        }
    }
}
