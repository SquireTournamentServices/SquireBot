use std::fmt;

#[derive(Debug, Copy, Clone)]
pub enum LookupError {
    TooMany,
    NotAny,
}

impl std::fmt::Display for LookupError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match &self {
            LookupError::TooMany => write!(f, "TooMany results in lookup."),
            LookupError::NotAny => write!(f, "No results in lookup."),
        }
    }
}

impl std::error::Error for LookupError {}
