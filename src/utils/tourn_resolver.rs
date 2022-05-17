use crate::model::lookup_error::LookupError;
use cycle_map::CycleMap;
use serenity::{framework::standard::macros::hook, model::channel::Message, prelude::Context};
use squire_core::tournament::TournamentId;

#[hook]
pub async fn tourn_id_resolver(
    ctx: &Context,
    msg: &Message,
    name: &str,
    name_and_id: &CycleMap<String, TournamentId>,
    mut ids: impl ExactSizeIterator<Item = TournamentId> + Send + 'fut,
) -> Option<TournamentId> {
    let length = ids.len();
    match length {
        0 => {
            let _ = msg
                .reply(
                    &ctx.http,
                    "There are no tournaments being held in this server.",
                )
                .await;
            None
        }
        1 => Some(ids.next().unwrap()),
        _ => {
            if let Some(t_id) = ids.find(|t_id| name_and_id.get_left(t_id).unwrap() == name) {
                Some(t_id)
            } else {
                let _ = msg
                    .reply(
                        &ctx.http,
                        "There is no tournament in this server with that name.",
                    )
                    .await;
                None
            }
        }
    }
}
