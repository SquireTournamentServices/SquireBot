use std::fmt::Display;

pub fn stringify_option<T>(o: Option<T>) -> String
where
    T: Display,
{
    match o {
        Some(v) => v.to_string(),
        None => String::from("None"),
    }
}

pub fn bool_from_string(s: &str) -> Option<bool> {
    match s {
        "t" | "T" | "true" | "True" | "1" => Some(true),
        "f" | "F" | "false" | "False" | "0" => Some(false),
        _ => None,
    }
}
