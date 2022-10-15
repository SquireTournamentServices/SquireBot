use std::borrow::Cow;

use serenity::{
    builder::CreateEmbed,
    client::Context,
    framework::standard::CommandResult,
    model::{channel::AttachmentType, prelude::Message},
};

pub mod confirmation;
pub mod consts;
pub mod containers;
pub mod guild_settings;
pub mod guild_tournament;
//pub mod misfortune;
pub mod guild_rounds;
pub mod tourn_settings_tree;

pub struct MessageContent {
    pub text: Option<Cow<'static, str>>,
    pub embeds: Option<Vec<CreateEmbed>>,
    pub attachment: Option<(String, tokio::fs::File)>,
}

impl MessageContent {
    pub fn empty() -> Self {
        Self {
            text: None,
            embeds: None,
            attachment: None,
        }
    }

    pub fn with_str(&mut self, text: &'static str) {
        self.text = Some(Cow::Borrowed(text));
    }

    pub fn with_text(&mut self, text: String) {
        self.text = Some(Cow::Owned(text));
    }
    pub fn with_embeds(&mut self, embeds: Vec<CreateEmbed>) {
        self.embeds = Some(embeds);
    }

    pub fn with_attachment(&mut self, name: String, attachment: tokio::fs::File) {
        self.attachment = Some((name, attachment));
    }

    pub async fn message_reply(self, ctx: &Context, msg: &Message) -> CommandResult {
        let mut resp = match self.text {
            Some(text) => msg.reply(&ctx.http, text).await?,
            None => msg.reply(&ctx.http, "\u{200b}").await?,
        };
        if let Some(embeds) = self.embeds {
            resp.edit(&ctx.http, |m| m.set_embeds(embeds)).await?;
        }
        if let Some((filename, file)) = self.attachment {
            resp.edit(&ctx.http, |m| {
                m.attachment(AttachmentType::File {
                    file: &file,
                    filename,
                })
            })
            .await?;
        }
        Ok(())
    }
}

impl Default for MessageContent {
    fn default() -> Self {
        Self::empty()
    }
}
