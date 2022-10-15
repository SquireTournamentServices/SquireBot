use serenity::builder::CreateEmbed;

pub mod confirmation;
pub mod consts;
pub mod containers;
pub mod guild_settings;
pub mod guild_tournament;
//pub mod misfortune;
pub mod guild_rounds;
pub mod tourn_settings_tree;

pub struct MessageContent {
    pub text: Option<String>,
    pub embeds: Option<Vec<CreateEmbed>>,
    pub attachment: Option<(String, tokio::fs::File)>,
}

impl MessageContent {
    pub fn new(text: String, embeds: Vec<CreateEmbed>) -> Self {
        Self {
            text: Some(text),
            embeds: Some(embeds),
            attachment: None,
        }
    }

    pub fn empty() -> Self {
        Self {
            text: None,
            embeds: None,
            attachment: None,
        }
    }

    pub fn with_text(&mut self, text: String) {
        self.text = Some(text);
    }
    pub fn with_embeds(&mut self, embeds: Vec<CreateEmbed>) {
        self.embeds = Some(embeds);
    }

    pub fn with_attachment(&mut self, name: String, attachment: tokio::fs::File) {
        self.attachment = Some((name, attachment));
    }
}

impl Default for MessageContent {
    fn default() -> Self {
        Self::empty()
    }
}
