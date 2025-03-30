use gimli::{DebugLine, DebugLineOffset, DwLne, LineInstruction, LittleEndian, Reader};
use object::{Object, ObjectSection};
use std::env;
use std::error::Error;
use std::fs;
use z3::{Config, Context, SatResult, Solver, ast::Ast};

#[derive(Clone, Copy, Debug)]
struct Constraint {
    off1: usize,
    off2: usize,
    op: Operation,
    expected: u8,
}

#[derive(Clone, Copy, Debug)]
enum Operation {
    Add,
    Sub,
    Mul,
    Xor,
}

/// Parse the ELF debuginfo, returing a list of checks and a flag length
fn parse_elf(data: &[u8]) -> Result<(Vec<Constraint>, usize), Box<dyn Error>> {
    let obj = object::File::parse(data)?;
    let section = obj
        .section_by_name(".debug_line")
        .ok_or("No .debug_line section found")?;
    let data = section.data()?;
    let debug_line = DebugLine::new(data, LittleEndian);
    let program = debug_line.program(DebugLineOffset(0), 8, None, None)?;
    let header = program.header();
    let mut instructions = header.instructions();

    let mut constraints = vec![];
    let mut flag_len = 0;
    loop {
        let Ok(Some(instr)) = instructions.next_instruction(&header) else {
            break;
        };
        match instr {
            // DW_LNE_set_flag
            LineInstruction::UnknownExtended(DwLne(0x51), mut args) => {
                flag_len = args.read_uleb128()?.max(flag_len);
            }
            LineInstruction::UnknownExtended(DwLne(0x52), mut args) => {
                constraints.push(Constraint {
                    off1: args.read_uleb128()? as usize,
                    off2: args.read_uleb128()? as usize,
                    op: match args.read_u8()? {
                        0 => Operation::Add,
                        1 => Operation::Sub,
                        2 => Operation::Mul,
                        3 => Operation::Xor,
                        x => Err(format!("invalid op `{x}`"))?,
                    },
                    expected: args.read_u8()?,
                });
            }
            _ => continue,
        }
    }
    Ok((constraints, flag_len as usize))
}

fn solve(constraints: &[Constraint], flag_len: usize) -> String {
    let config = Config::new();
    let ctx = Context::new(&config);
    let solver = Solver::new(&ctx);
    let flag: Vec<_> = (0..=flag_len)
        .map(|i| z3::ast::BV::new_const(&ctx, format!("flag_{i}"), 8))
        .collect();
    for constraint in constraints {
        let v1 = &flag[constraint.off1];
        let v2 = &flag[constraint.off2];
        let res = match constraint.op {
            Operation::Add => v1 + v2,
            Operation::Sub => v1 - v2,
            Operation::Mul => v1 * v2,
            Operation::Xor => v1 ^ v2,
        };
        solver.assert(&res._eq(&z3::ast::BV::from_u64(&ctx, constraint.expected as u64, 8)));
    }
    let model = match solver.check() {
        SatResult::Sat => solver.get_model().unwrap(),
        _ => panic!("no solution found"),
    };
    let mut out = vec![];
    for b in flag {
        out.push(model.eval(&b, true).unwrap().as_u64().unwrap() as u8);
    }
    String::from_utf8_lossy(&out).to_string()
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <input ELF>", args[0]);
        std::process::exit(1);
    }
    let file_data = fs::read(&args[1])?;
    let (constraints, flag_len) = parse_elf(&file_data)?;
    println!("[+] Flag: {}", solve(&constraints, flag_len));
    Ok(())
}
