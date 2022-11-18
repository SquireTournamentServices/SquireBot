use std::{borrow::Cow, io::SeekFrom};

use itertools::Itertools;
use serenity::{
    builder::CreateEmbed,
    client::Context,
    framework::standard::CommandResult,
    model::{channel::AttachmentType, prelude::Message},
};
use tokio::io::AsyncSeekExt;

pub mod confirmation;
pub mod consts;
pub mod containers;
pub mod guilds;
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
            let len = embeds.len();
            let chunks = embeds
                .into_iter()
                .chunks(10)
                .into_iter()
                .map(|c| c.into_iter().collect_vec())
                .collect_vec();
            match len {
                1 => {
                    resp.edit(&ctx.http, |m| {
                        m.set_embeds(chunks.into_iter().next().unwrap())
                    })
                    .await?;
                }
                _ => {
                    for chunk in chunks.into_iter() {
                        let mut resp = msg.reply(&ctx.http, "\u{200b}").await?;
                        resp.edit(&ctx.http, |m| m.set_embeds(chunk)).await?;
                    }
                }
            }
        }
        if let Some((filename, mut file)) = self.attachment {
            file.seek(SeekFrom::Start(0)).await.unwrap();
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
