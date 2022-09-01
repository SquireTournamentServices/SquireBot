use std::{collections::HashSet, ops::RangeBounds};

use itertools::Itertools;
use serenity::builder::CreateEmbed;

use mtgjson::model::{abstract_card::AbstractCard, card_attribute::CardFace};
use squire_lib::player::Deck;

static CREATURE: &str = "Creature";
static LAND: &str = "Land";
static ARTIFACT: &str = "Artifact";
static ENCHANTMENT: &str = "Enchantment";
static INSTANT: &str = "Instant";
static SORCERY: &str = "Sorcery";
static PLANESWALKER: &str = "Planeswalker";

/// A compact deck format used to help "pretty print" a deck.
/// Commanders and sideboards are not sorted
pub struct TypeSortedDeck {
    pub commanders: HashSet<String>,
    pub lands: HashSet<(usize, String)>,
    pub creatures: HashSet<(usize, String)>,
    pub artifacts: HashSet<(usize, String)>,
    pub enchantments: HashSet<(usize, String)>,
    pub instants: HashSet<(usize, String)>,
    pub sorceries: HashSet<(usize, String)>,
    pub planewalkers: HashSet<(usize, String)>,
    pub other: HashSet<(usize, String)>,
    pub sideboard: HashSet<(usize, String)>,
}

/// Cards with multiple card type, will be counted only once and will only use their front face.
/// The preference for this is as follows:
///  - Creature
///  - Land
///  - Artifact
///  - Enchantment
///  - Instant
///  - Sorcery
///  - Planeswalker
impl From<Deck> for TypeSortedDeck {
    fn from(mut deck: Deck) -> Self {
        let mut lands: HashSet<(usize, String)> = HashSet::new();
        let mut creatures: HashSet<(usize, String)> = HashSet::new();
        let mut artifacts: HashSet<(usize, String)> = HashSet::new();
        let mut enchantments: HashSet<(usize, String)> = HashSet::new();
        let mut instants: HashSet<(usize, String)> = HashSet::new();
        let mut sorceries: HashSet<(usize, String)> = HashSet::new();
        let mut planewalkers: HashSet<(usize, String)> = HashSet::new();
        let mut other: HashSet<(usize, String)> = HashSet::new();
        for (card, count) in deck.mainboard.drain() {
            if card.front_face.types.contains(CREATURE) {
                creatures.insert((count, card.get_name()));
            } else if card.front_face.types.contains(LAND) {
                lands.insert((count, card.get_name()));
            } else if card.front_face.types.contains(ARTIFACT) {
                artifacts.insert((count, card.get_name()));
            } else if card.front_face.types.contains(ENCHANTMENT) {
                enchantments.insert((count, card.get_name()));
            } else if card.front_face.types.contains(INSTANT) {
                instants.insert((count, card.get_name()));
            } else if card.front_face.types.contains(SORCERY) {
                sorceries.insert((count, card.get_name()));
            } else if card.front_face.types.contains(PLANESWALKER) {
                planewalkers.insert((count, card.get_name()));
            } else {
                other.insert((count, card.get_name()));
            }
        }
        let commanders = deck.commanders.drain().map(|(c, n)| c.get_name()).collect();
        let sideboard = deck
            .sideboard
            .drain()
            .map(|(c, n)| (n, c.get_name()))
            .collect();

        Self {
            commanders,
            lands,
            creatures,
            artifacts,
            enchantments,
            instants,
            sorceries,
            planewalkers,
            other,
            sideboard,
        }
    }
}

impl TypeSortedDeck {
    pub fn populate_embed<'a>(&self, mut e: &'a mut CreateEmbed) -> &'a mut CreateEmbed {
        if !self.lands.is_empty() {
            e.field(
                format!("Land ({}):", self.count_lands()),
                self.lands
                    .iter()
                    .map(|(n, c)| format!("{n} {c}"))
                    .join("\n"),
                true,
            );
        }
        if !self.creatures.is_empty() {
            e.field(
                format!("Creature ({}):", self.count_creatures()),
                self.creatures
                    .iter()
                    .map(|(n, c)| format!("{n} {c}"))
                    .join("\n"),
                true,
            );
        }
        if !self.artifacts.is_empty() {
            e.field(
                format!("Artifacts ({}):", self.count_artifacts()),
                self.artifacts
                    .iter()
                    .map(|(n, c)| format!("{n} {c}"))
                    .join("\n"),
                true,
            );
        }
        if !self.enchantments.is_empty() {
            e.field(
                format!("Enchantments ({}):", self.count_enchantments()),
                self.enchantments
                    .iter()
                    .map(|(n, c)| format!("{n} {c}"))
                    .join("\n"),
                true,
            );
        }
        if !self.instants.is_empty() {
            e.field(
                format!("Instant ({}):", self.count_instants()),
                self.instants
                    .iter()
                    .map(|(n, c)| format!("{n} {c}"))
                    .join("\n"),
                true,
            );
        }
        if !self.sorceries.is_empty() {
            e.field(
                format!("Sorceries ({}):", self.count_sorceries()),
                self.sorceries
                    .iter()
                    .map(|(n, c)| format!("{n} {c}"))
                    .join("\n"),
                true,
            );
        }
        if !self.planewalkers.is_empty() {
            e.field(
                format!("Planewalkers ({}):", self.count_planeswalkers()),
                self.planewalkers
                    .iter()
                    .map(|(n, c)| format!("{n} {c}"))
                    .join("\n"),
                true,
            );
        }
        if !self.other.is_empty() {
            e.field(
                format!("Others ({}):", self.count_other()),
                self.other
                    .iter()
                    .map(|(n, c)| format!("{n} {c}"))
                    .join("\n"),
                true,
            );
        }
        if !self.sideboard.is_empty() {
            e.field(
                format!("Sideboard ({}):", self.count_sideboard()),
                self.sideboard
                    .iter()
                    .map(|(n, c)| format!("{n} {c}"))
                    .join("\n"),
                true,
            );
        }
        e
    }

    pub fn count_all(&self) -> usize {
        self.count_commanders()
            + self.count_lands()
            + self.count_creatures()
            + self.count_artifacts()
            + self.count_enchantments()
            + self.count_instants()
            + self.count_sorceries()
            + self.count_sideboard()
    }
    pub fn count_commanders(&self) -> usize {
        self.commanders.len()
    }
    pub fn count_lands(&self) -> usize {
        self.lands.iter().map(|(n, _)| n).sum()
    }
    pub fn count_creatures(&self) -> usize {
        self.creatures.iter().map(|(n, _)| n).sum()
    }
    pub fn count_artifacts(&self) -> usize {
        self.artifacts.iter().map(|(n, _)| n).sum()
    }
    pub fn count_enchantments(&self) -> usize {
        self.enchantments.iter().map(|(n, _)| n).sum()
    }
    pub fn count_instants(&self) -> usize {
        self.instants.iter().map(|(n, _)| n).sum()
    }
    pub fn count_sorceries(&self) -> usize {
        self.sorceries.iter().map(|(n, _)| n).sum()
    }
    pub fn count_planeswalkers(&self) -> usize {
        self.sorceries.iter().map(|(n, _)| n).sum()
    }
    pub fn count_other(&self) -> usize {
        self.sorceries.iter().map(|(n, _)| n).sum()
    }
    pub fn count_sideboard(&self) -> usize {
        self.sideboard.iter().map(|(n, _)| n).sum()
    }
}
