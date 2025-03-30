use anyhow::Result;
use rand::seq::IteratorRandom;
use std::env;
use std::path::Path;

use gen_elf::{check_flag_ins, set_flag_ins};

fn flag_checker_program() -> Vec<u8> {
    let correct_flag = b"dice{h1ghly_sp3c_c0mpl14nt_dw4rf_p4rs3r}";
    // If RELEASE is not set, embed the correct flag
    let static_flag = if std::env::var("RELEASE").is_ok() {
        correct_flag
            .iter()
            .enumerate()
            .map(|(i, c)| {
                if i <= 4 || i == correct_flag.len() - 1 {
                    *c
                } else {
                    b'X'
                }
            })
            .collect()
    } else {
        correct_flag.to_vec()
    };

    let mut set_flag = vec![];
    for (i, c) in static_flag.iter().enumerate() {
        set_flag.extend_from_slice(&set_flag_ins(i as u64, *c));
    }

    let mut constraints = vec![];
    let n_constraints = (correct_flag.len() as u64).ilog2();
    for (i, c) in correct_flag.iter().enumerate() {
        for (j, c2) in correct_flag
            .iter()
            .enumerate()
            .choose_multiple(&mut rand::rng(), n_constraints as usize)
        {
            let (opcode, expected) = match rand::random_range(0..=3) {
                0 => (0, c.wrapping_add(*c2)),
                1 => (1, c.wrapping_sub(*c2)),
                2 => (2, c.wrapping_mul(*c2)),
                3 => (3, c ^ c2),
                _ => unreachable!(),
            };
            constraints.extend_from_slice(&check_flag_ins(i as u64, j as u64, opcode, expected));
        }
    }

    set_flag.append(&mut constraints);
    set_flag
}

fn main() -> Result<()> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 3 {
        println!("Usage: {} <input ELF> <output ELF>", args[0]);
        return Ok(());
    }
    let input_path = Path::new(&args[1]);
    let output_path = Path::new(&args[2]);

    gen_elf::rebuild_elf(input_path, output_path, &flag_checker_program())?;
    Ok(())
}
