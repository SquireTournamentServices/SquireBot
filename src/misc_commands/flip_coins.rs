use serenity::framework::standard::{macros::command, Args, CommandResult};
use serenity::model::prelude::*;
use serenity::prelude::*;

use rand::{Rng, SeedableRng};
use rand::prelude::*;

pub const MAX_COIN_FLIPS: u64 = 10_000_000;
pub const MAX_KRARK_THUMBS: u64 = 32;

#[command("flip-coins")]
#[only_in(guild)]
#[sub_commands(krark)]
#[delimiters(" ")]	
#[min_args(1)]
#[max_args(1)]
#[description("Flips N coins.")]
async fn flip_coins(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let mut i = args.iter::<u64>();
    match i.next().unwrap() {
        Err(_) => {
            msg.reply( &ctx.http, "Please specify a whole, position number using digits." ).await?;
        },
        Ok(val) => {
            if val > MAX_COIN_FLIPS {
                msg.reply(&ctx.http, format!("You specified too many flips. The can specify at most {} flips", MAX_COIN_FLIPS)).await?;
            } else {
                msg.reply(&ctx.http, format!("Out of {} flips, you won {} many.", val, coin_flips(val, 0))).await?;
            }
        }
    }
    Ok(())
}

#[command]
#[only_in(guild)]
#[delimiters(" ")]	
#[min_args(2)]
#[max_args(2)]
#[description("While K Krark's Thumbs are out, flips N coins.")]
async fn krark(ctx: &Context, msg: &Message, mut args: Args) -> CommandResult {
    let mut i = args.iter::<u64>();
    match i.next().unwrap() {
        Err(_) => {
            msg.reply( &ctx.http, "Please specify a whole, position number using digits." ).await?;
        },
        Ok(mut val) => {
            match i.next().unwrap() {
                Err(_) => {
                    msg.reply( &ctx.http, "Please specify a whole, position number using digits." ).await?;
                },
                Ok(k) => {
                    if k > MAX_KRARK_THUMBS {
                        msg.reply(&ctx.http, format!("You specified too many thumbs. You can specify at most {} thumbs.", MAX_KRARK_THUMBS)).await?;
                    } else if val*k > MAX_COIN_FLIPS {
                        msg.reply(&ctx.http, format!("You specified too many flips. You can specify at most {} flips.", MAX_COIN_FLIPS/k)).await?;
                    } else {
                        msg.reply(&ctx.http, format!("Out of {} flips, you won {} many.", val, coin_flips(val, k))).await?;
                    }
                }
            }
        }
    }
    Ok(())
}

fn coin_flips(mut flips: u64, mut krark: u64) -> u64 {
    // Change # of Krark's Thumbs into the total number of "choice" flips to
    // replace each coin flips with, which is equal to 2^krark.
    if krark > 0 {
        krark = 1u64 << krark;
    }

    // Set up random number gen
    let mut rng = rand::thread_rng();
    let mut rand_bits: u64 = rng.gen();

    let mut digest: u64 = 0;

    while flips >= 64 {
        // Flip extra "choice" coins, if applicable
        rand_bits = rng.gen();
        for _ in 1..krark {
            rand_bits |= rng.gen::<u64>();
        }
        digest += rand_bits.count_ones() as u64;
        flips -= 64;
    }
    
    if flips > 0 {
        for _ in 1..krark {
            rand_bits |= rng.gen::<u64>();
        }
        digest += (rand_bits << (64 - flips) ).count_ones() as u64;
    }

    // Remove the guaranteed wins from earlier to get the true win count
    digest
}
