use anyhow::Result;
use bytemuck::{Pod, Zeroable};
use gimli::leb128;
use object::build::elf::SectionData;
use std::fs::{self, OpenOptions};
use std::os::unix::fs::OpenOptionsExt;
use std::path::Path;

#[allow(non_upper_case_globals)]
const DW_LNE_set_flag: u8 = 0x51;
#[allow(non_upper_case_globals)]
const DW_LNE_check_flag: u8 = 0x52;

#[derive(Copy, Clone, Pod, Zeroable, Debug)]
#[repr(C, packed)]
struct LineProgramHeader {
    unit_length: u32,
    version: u16,
    header_length: u32,
    minimum_instruction_length: u32,
    maximum_operations_per_instruction: u8,
    default_is_stmt: u8,
    line_base: i8,
    line_range: u8,
    opcode_base: u8,
}

pub fn generate_extended_ins(content: &[u8]) -> Vec<u8> {
    let mut ins = vec![];
    ins.push(0);
    leb128::write::unsigned(&mut ins, content.len() as u64).unwrap();
    ins.extend_from_slice(content);
    ins
}

pub fn set_flag_ins(off: u64, c: u8) -> Vec<u8> {
    let mut ins = vec![DW_LNE_set_flag];
    leb128::write::unsigned(&mut ins, off).unwrap();
    ins.push(c);
    generate_extended_ins(&ins)
}

pub fn check_flag_ins(off1: u64, off2: u64, opc: u8, expected: u8) -> Vec<u8> {
    let mut ins = vec![DW_LNE_check_flag];
    leb128::write::unsigned(&mut ins, off1).unwrap();
    leb128::write::unsigned(&mut ins, off2).unwrap();
    ins.push(opc);
    ins.push(expected);
    generate_extended_ins(&ins)
}

fn modify_debug_line_section(mut data: &[u8], program: &[u8]) -> Result<Vec<u8>> {
    let mut new_section = Vec::new();
    let mut unit_index = 0;
    while !data.is_empty() {
        let header: LineProgramHeader =
            *bytemuck::from_bytes(&data[..std::mem::size_of::<LineProgramHeader>()]);
        if header.version != 4 {
            panic!("dwarf v4 required");
        }
        let total_unit_length = (header.unit_length + 4) as usize;
        if unit_index != 0 {
            new_section.extend_from_slice(&data[..total_unit_length]);
        } else {
            let (header_bytes, instructions) = data.split_at(header.header_length as usize);
            let mut new_header = header_bytes.to_vec();
            let mut new_instructions = instructions.to_vec();
            // Insert before end-of-sequence
            let point = instructions.len() - 3;
            new_instructions.splice(point..point, program.iter().copied());
            let header: &mut LineProgramHeader = bytemuck::from_bytes_mut(
                &mut new_header[..std::mem::size_of::<LineProgramHeader>()],
            );
            header.unit_length += (new_instructions.len() - instructions.len()) as u32;
            new_section.extend_from_slice(&new_header);
            new_section.extend_from_slice(&new_instructions);
        }
        unit_index += 1;
        (_, data) = data.split_at(total_unit_length);
    }
    Ok(new_section)
}

pub fn rebuild_elf(input_path: &Path, output_path: &Path, program: &[u8]) -> Result<()> {
    let file_data = fs::read(input_path)?;
    let mut builder = object::build::elf::Builder::read(file_data.as_slice())?;

    for section in &mut builder.sections {
        if section.name.as_slice() == b".debug_line" {
            let SectionData::Data(data) = &mut section.data else {
                unreachable!()
            };
            *data = modify_debug_line_section(data.as_slice(), program)?.into();
        }
    }
    let file = OpenOptions::new()
        .create(true)
        .truncate(true)
        .write(true)
        .mode(0o755)
        .open(output_path)?;
    let mut buffer = object::write::StreamingBuffer::new(file);
    builder.write(&mut buffer)?;
    Ok(())
}
