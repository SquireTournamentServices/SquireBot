use std::collections::{HashMap, HashSet};

use serde::{Deserialize, Serialize};

use serenity::model::{guild::Role, id::GuildId};

use squire_lib::{identifiers::TournamentId, tournament::TournamentPreset};

mod guild_settings;
pub use guild_settings::{
    get_default_judge_role_id, get_default_matches_category_id, get_default_pairings_channel_id,
    get_default_tourn_admin_role_id, GuildSettings,
};

mod guild_rounds;
pub use guild_rounds::{GuildRound, GuildRoundData, TimerWarnings, TrackingRound};

mod guild_tournament;
pub use guild_tournament::{GuildTournament, GuildTournamentAction, SquireTournamentSetting};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GuildTournRegistry {
    guild_id: GuildId,
    pub settings: GuildSettings,
    pub tourns: HashMap<TournamentId, GuildTournament>,
    pub past_tourns: HashSet<TournamentId>,
}

impl GuildTournRegistry {
    pub fn new(id: GuildId) -> Self {
        Self {
            guild_id: id,
            settings: GuildSettings::new(id),
            tourns: HashMap::new(),
            past_tourns: HashSet::new(),
        }
    }

    pub fn get_tourn(&self, name: &str) -> Option<&GuildTournament> {
        match self.tourns.len() {
            0 => None,
            1 => self.tourns.values().next(),
            _ => self.tourns.values().find(|t| t.tourn.name == name),
        }
    }

    pub fn get_tourn_mut(&mut self, name: &str) -> Option<&mut GuildTournament> {
        match self.tourns.len() {
            0 => None,
            1 => self.tourns.values_mut().next(),
            _ => self.tourns.values_mut().find(|t| t.tourn.name == name),
        }
    }

    pub async fn create_tourn(
        &mut self,
        tourn_role: Role,
        preset: TournamentPreset,
        name: String,
    ) -> bool {
        match self.get_tourn(&name) {
            Some(_) => false,
            None => match self.settings.create_tournament(tourn_role, preset, name) {
                Some(tourn) => {
                    self.tourns.insert(tourn.tourn.id, tourn);
                    true
                }
                None => false,
            },
        }
    }

    pub async fn remove_tourn(&mut self, id: &TournamentId) -> Option<GuildTournament> {
        let tourn = self.tourns.remove(id)?;
        self.past_tourns.insert(tourn.tourn.id);
        Some(tourn)
    }
}

/*
impl Serialize for GuildTournRegistry {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        let mut state = serializer.serialize_struct("GuildTournRegistry", 4)?;
        state.serialize_field("guild_id", &self.guild_id)?;
        state.serialize_field("settings", &self.settings)?;
        let tourns: Vec<_> = self.tourns.values().map(|t| t.blocking_read()).collect();
        let tourns: HashMap<_, _> = tourns.iter().map(|t| (t.tourn.id, &**t)).collect();
        state.serialize_field("tourns", &tourns)?;
        state.serialize_field("past_tourns", &self.past_tourns)?;
        state.end()
    }
}

impl<'de> Deserialize<'de> for GuildTournRegistry {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        enum Field {
            GuildId,
            Settings,
            Tourns,
            PastTourns,
        }

        impl<'de> Deserialize<'de> for Field {
            fn deserialize<D>(deserializer: D) -> Result<Field, D::Error>
            where
                D: Deserializer<'de>,
            {
                struct FieldVisitor;

                impl<'de> Visitor<'de> for FieldVisitor {
                    type Value = Field;

                    fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
                        formatter.write_str("`guild_id`, `settings`, `tourns`, or `past_tourns`")
                    }

                    fn visit_str<E>(self, value: &str) -> Result<Field, E>
                    where
                        E: de::Error,
                    {
                        match value {
                            "guild_id" => Ok(Field::GuildId),
                            "settings" => Ok(Field::Settings),
                            "tourns" => Ok(Field::Tourns),
                            "past_tourns" => Ok(Field::PastTourns),
                            _ => Err(de::Error::unknown_field(value, FIELDS)),
                        }
                    }
                }

                deserializer.deserialize_identifier(FieldVisitor)
            }
        }

        struct GuildTournRegistryVisitor;

        impl<'de> Visitor<'de> for GuildTournRegistryVisitor {
            type Value = GuildTournRegistry;

            fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
                formatter.write_str("struct GuildTournRegistry")
            }

            fn visit_seq<V>(self, mut seq: V) -> Result<GuildTournRegistry, V::Error>
            where
                V: SeqAccess<'de>,
            {
                let guild_id = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(0, &self))?;
                let settings = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(0, &self))?;
                let tourns: HashMap<_, GuildTournament> = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(0, &self))?;
                let tourns = tourns
                    .into_iter()
                    .map(|(id, t)| (id, Arc::new(RwLock::new(t))))
                    .collect();
                let past_tourns = seq
                    .next_element()?
                    .ok_or_else(|| de::Error::invalid_length(0, &self))?;
                Ok(GuildTournRegistry {
                    guild_id,
                    settings,
                    tourns,
                    past_tourns,
                })
            }

            fn visit_map<V>(self, mut map: V) -> Result<GuildTournRegistry, V::Error>
            where
                V: MapAccess<'de>,
            {
                let mut guild_id = None;
                let mut settings = None;
                let mut tourns: Option<HashMap<_, GuildTournament>> = None;
                let mut past_tourns = None;
                while let Some(key) = map.next_key()? {
                    match key {
                        Field::GuildId => {
                            if guild_id.is_some() {
                                return Err(de::Error::duplicate_field("guild_id"));
                            }
                            guild_id = Some(map.next_value()?);
                        }
                        Field::Settings => {
                            if settings.is_some() {
                                return Err(de::Error::duplicate_field("settings"));
                            }
                            settings = Some(map.next_value()?);
                        }
                        Field::Tourns => {
                            if tourns.is_some() {
                                return Err(de::Error::duplicate_field("tourns"));
                            }
                            tourns = Some(map.next_value()?);
                        }
                        Field::PastTourns => {
                            if past_tourns.is_some() {
                                return Err(de::Error::duplicate_field("past_tourns"));
                            }
                            past_tourns = Some(map.next_value()?);
                        }
                    }
                }
                let guild_id = guild_id.ok_or_else(|| de::Error::missing_field("guild_id"))?;
                let settings = settings.ok_or_else(|| de::Error::missing_field("settings"))?;
                let tourns = tourns
                    .ok_or_else(|| de::Error::missing_field("tourns"))?
                    .into_iter()
                    .map(|(id, t)| (id, Arc::new(RwLock::new(t))))
                    .collect();
                let past_tourns =
                    past_tourns.ok_or_else(|| de::Error::missing_field("past_tourns"))?;
                Ok(GuildTournRegistry {
                    guild_id,
                    settings,
                    tourns,
                    past_tourns,
                })
            }
        }

        const FIELDS: &'static [&'static str] = &["guild_id", "settings", "tourns", "past_tourns"];
        deserializer.deserialize_struct("GuildTournRegistry", FIELDS, GuildTournRegistryVisitor)
    }
}
*/
