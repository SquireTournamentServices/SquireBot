pub fn stringify_option<T>(o: Option<T>) -> String
where
    T: ToString,
{
    match o {
        Some(v) => v.to_string(),
        None => String::from("None"),
    }
}
