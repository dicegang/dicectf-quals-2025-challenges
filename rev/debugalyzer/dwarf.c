#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <libelf.h>
#include <gelf.h>

// #define DEBUG 1

int main(int argc, char **argv);

typedef struct
{
    uint64_t address;
    uint32_t op_index;
    uint32_t file;
    uint32_t line;
    uint32_t column;
    bool is_stmt;
    bool basic_block;
    bool end_sequence;
    bool prologue_end;
    bool epilogue_begin;
    uint32_t isa;
    uint32_t discriminator;
} DwarfLineState;

typedef struct
{
    uint8_t minimum_instruction_length;
    int8_t line_base;
    uint8_t line_range;
    uint8_t opcode_base;
} DwarfLineProgramHeader;

enum FlagOp
{
    OP_ADD = 0,
    OP_SUB = 1,
    OP_MUL = 2,
    OP_XOR = 3,
};

static uint64_t read_uleb128(const uint8_t **data, size_t *size)
{
    uint64_t result = 0;
    int shift = 0;
    while (*size)
    {
        uint8_t byte = **data;
        (*data)++;
        (*size)--;
        result |= ((uint64_t)(byte & 0x7F)) << shift;
        if ((byte & 0x80) == 0)
            break;
        shift += 7;
    }
    return result;
}

static int64_t read_sleb128(const uint8_t **data, size_t *size)
{
    int64_t result = 0;
    int shift = 0;
    uint8_t byte = 0;
    do
    {
        byte = **data;
        (*data)++;
        (*size)--;
        result |= ((int64_t)(byte & 0x7F)) << shift;
        shift += 7;
    } while ((byte & 0x80) && *size);
    if ((shift < 64) && (byte & 0x40))
        result |= -((int64_t)1 << shift);
    return result;
}

static void emit_state(const DwarfLineState *state)
{
#if DEBUG
    printf("State: address=%llu, line=%u, file=%u, column=%u, is_stmt=%d, basic_block=%d, prologue_end=%d, epilogue_begin=%d, isa=%u, discriminator=%u, end_sequence=%d\n",
           state->address, state->line, state->file, state->column, state->is_stmt,
           state->basic_block, state->prologue_end, state->epilogue_begin,
           state->isa, state->discriminator, state->end_sequence);
#endif
}


// contrived vvvvvv
char flag[64] = {0};
char correct_msg[] = "Flag is correct!";
char incorrect_msg[] = "Flag is incorrect!";
char *__attribute__((noinline)) select_str(char *msg_a, char *msg_b, uint8_t which)
{
    char *msgs[] = {msg_a, msg_b};
    return msgs[which ? 1 : 0];
}
// contrived ^^^^^

void execute_dwarf_bytecode_v4(const uint8_t *data, size_t size, const DwarfLineProgramHeader *header, uint8_t default_is_stmt, uint8_t address_size)
{
    DwarfLineState state = {0};
    memset(flag, sizeof(flag), 0);
    int flag_ok = 1;
    state.line = 1;
    state.is_stmt = default_is_stmt ? true : false;
    while (size)
    {
        uint8_t opcode = *data;
        data++;
        size--;
        // Extended opcodes
        if (opcode == 0)
        {
            uint64_t ext_len = read_uleb128(&data, &size);
            if (size == 0)
                break;
            uint8_t ext_opcode = *data;
            data++;
            size--;
            switch (ext_opcode)
            {
            case 1: // DW_LNE_end_sequence
                state.end_sequence = true;
                emit_state(&state);
                state = (DwarfLineState){0};
                state.line = 1;
                state.is_stmt = default_is_stmt ? true : false;
                break;
            case 2:
            { // DW_LNE_set_address
                if (ext_len < address_size + 1)
                    break;
                uint64_t addr = 0;
                for (size_t i = 0; i < address_size; i++)
                    addr |= ((uint64_t)data[i]) << (8 * i);
                state.address = addr;
                data += address_size;
                size -= address_size;
                break;
            }
            case 0x51:
            { // DW_LNE_set_flag
                int off = read_uleb128(&data, &size);
                if (size == 0)
                    break;
                uint8_t val = *data;
                data++;
                size--;
                flag[off] = val;
                break;
            }
            case 0x52:
            { // DW_LNE_check_flag
                int off1 = read_uleb128(&data, &size);
                if (size == 0)
                    break;
                uint8_t f1 = flag[off1];

                int off2 = read_uleb128(&data, &size);
                if (size == 0)
                    break;
                uint8_t f2 = flag[off2];

                uint8_t op = *data;
                data++;
                size--;
                if (size == 0)
                    break;

                uint8_t res;
                switch (op)
                {
                case OP_ADD:
                    res = f1 + f2;
                    break;
                case OP_SUB:
                    res = f1 - f2;
                    break;
                case OP_MUL:
                    res = f1 * f2;
                    break;
                case OP_XOR:
                    res = f1 ^ f2;
                    break;
                default:
                    res = 0;
                    break;
                }

                uint8_t expected = *data;
                data++;
                size--;
                if (size == 0)
                    break;
                if (res != expected)
                {
#if DEBUG
                    printf("flag[%d] (%d) flag[%d] != %d\n", off1, op, off2, expected);
#endif
                    flag_ok = 0;
                }

                break;
            }
            // Unimplemented
            default:
                printf("Extended opcode %d unimplemented\n", opcode);
                while (ext_len > 1 && size)
                {
                    data++;
                    size--;
                    ext_len--;
                }
                break;
            }
        }
        else if (opcode < header->opcode_base)
        {
            switch (opcode)
            {
            case 1: // DW_LNS_copy
                emit_state(&state);
                state.basic_block = false;
                state.prologue_end = false;
                state.epilogue_begin = false;
                state.discriminator = 0;
                break;
            case 2:
            { // DW_LNS_advance_pc
                uint64_t operand = read_uleb128(&data, &size);
                state.address += operand * header->minimum_instruction_length;
                break;
            }
            case 3:
            { // DW_LNS_advance_line
                int64_t operand = read_sleb128(&data, &size);
                state.line += operand;
                break;
            }
            case 4: // DW_LNS_set_file
                state.file = (uint32_t)read_uleb128(&data, &size);
                break;
            case 5: // DW_LNS_set_column
                state.column = (uint32_t)read_uleb128(&data, &size);
                break;
            case 6: // DW_LNS_negate_stmt
                state.is_stmt = !state.is_stmt;
                break;
            case 7: // DW_LNS_set_basic_block
                state.basic_block = true;
                break;
            case 8:
            { // DW_LNS_const_add_pc
                uint8_t adjusted_opcode = 255 - header->opcode_base;
                uint64_t addr_incr = (adjusted_opcode / header->line_range) * header->minimum_instruction_length;
                state.address += addr_incr;
                break;
            }
            case 9:
            { // DW_LNS_fixed_advance_pc
                if (size < 2)
                    break;
                uint16_t operand = data[0] | (data[1] << 8);
                state.address += operand;
                data += 2;
                size -= 2;
                break;
            }
            case 10: // DW_LNS_prologue_end
                state.prologue_end = true;
                break;
            case 11: // DW_LNS_set_epilogue_begin
                state.epilogue_begin = true;
                break;
            case 12: // DW_LNS_set_isa
                state.isa = (uint32_t)read_uleb128(&data, &size);
                break;
            default:
                printf("Opcode %d unimplemented\n", opcode);
                break;
            }
        }
        else
        {
            uint8_t adjusted_opcode = opcode - header->opcode_base;
            uint64_t addr_incr = (adjusted_opcode / header->line_range) * header->minimum_instruction_length;
            int64_t line_incr = header->line_base + (adjusted_opcode % header->line_range);
            state.address += addr_incr;
            state.line += line_incr;
            emit_state(&state);
            state.basic_block = false;
            state.prologue_end = false;
            state.epilogue_begin = false;
            state.discriminator = 0;
        }
    }
#if DEBUG
    printf("The flag is %s\n", flag);
#endif

    // Horrible horrible code to make these strings writable alend rsi controllab
    puts(select_str(incorrect_msg, correct_msg, flag_ok));
}

typedef struct
{
    uint32_t unit_length;
    uint16_t version;
    uint32_t header_length;
    uint8_t minimum_instruction_length;
    uint8_t maximum_operations_per_instruction;
    uint8_t default_is_stmt;
    int8_t line_base;
    uint8_t line_range;
    uint8_t opcode_base;
    size_t header_size;
    size_t total_unit_size;
    uint8_t address_size;
} DebugLineUnit;

static int parse_debug_line_unit_v4(const uint8_t *data, size_t size, DebugLineUnit *unit, uint8_t address_size)
{
    if (size < 10)
    {
        return -1;
    }
    uint32_t unit_length = data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24);
    size_t total_unit_size = unit_length + 4;
    if (size < total_unit_size)
    {
        return -1;
    }
    unit->unit_length = unit_length;
    unit->total_unit_size = total_unit_size;
    unit->version = data[4] | (data[5] << 8);
    unit->header_length = data[6] | (data[7] << 8) | (data[8] << 16) | (data[9] << 24);
    size_t header_end = 10 + unit->header_length;
    if (total_unit_size < header_end)
    {
        return -1;
    }
    if (header_end < 16)
    {
        return -1;
    }
    unit->minimum_instruction_length = data[10];
    unit->maximum_operations_per_instruction = data[11];
    unit->default_is_stmt = data[12];
    unit->line_base = (int8_t)data[13];
    unit->line_range = data[14];
    unit->opcode_base = data[15];
    size_t offset = 16;
    if (unit->opcode_base > 0)
        offset += (unit->opcode_base - 1);
    while (offset < header_end)
    {
        size_t len = strlen((const char *)(data + offset));
        offset += len + 1;
        if (len == 0)
            break;
    }
    while (offset < header_end)
    {
        size_t len = strlen((const char *)(data + offset));
        offset += len + 1;
        if (len == 0)
            break;
        for (int i = 0; i < 3; i++)
        {
            while (offset < header_end)
            {
                uint8_t byte = data[offset];
                offset++;
                if ((byte & 0x80) == 0)
                    break;
            }
        }
    }
    if (offset != header_end)
        return -1;
    unit->header_size = header_end;
    unit->address_size = address_size;
    return 0;
}

static void process_debug_line_section_v4(const uint8_t *data, size_t size, uint8_t address_size)
{
    size_t offset = 0;
    while (offset < size)
    {
        DebugLineUnit unit;
        if (parse_debug_line_unit_v4(data + offset, size - offset, &unit, address_size) != 0)
        {
            break;
        }
        size_t instructions_length = unit.total_unit_size - unit.header_size;
        DwarfLineProgramHeader dwarf_header;
        dwarf_header.minimum_instruction_length = unit.minimum_instruction_length;
        dwarf_header.line_base = unit.line_base;
        dwarf_header.line_range = unit.line_range;
        dwarf_header.opcode_base = unit.opcode_base;
        printf("Processing .debug_line unit: total_size=%zu, header_size=%zu, instructions_length=%zu\n",
               unit.total_unit_size, unit.header_size, instructions_length);
        execute_dwarf_bytecode_v4(data + offset + unit.header_size, instructions_length, &dwarf_header, unit.default_is_stmt, unit.address_size);
        offset += unit.total_unit_size;
    }
}

int main(int argc, char **argv)
{
    setbuf(stdout, NULL);
    if (argc < 2)
    {
        fprintf(stderr, "Usage: %s <elf-file>\n", argv[0]);
        return EXIT_FAILURE;
    }
    if (elf_version(EV_CURRENT) == EV_NONE)
    {
        fprintf(stderr, "ELF library initialization failed\n");
        return EXIT_FAILURE;
    }
    int fd = open(argv[1], O_RDONLY);
    if (fd < 0)
    {
        perror("open");
        return EXIT_FAILURE;
    }
    Elf *elf = elf_begin(fd, ELF_C_READ, NULL);
    if (!elf)
    {
        fprintf(stderr, "elf_begin() failed\n");
        close(fd);
        return EXIT_FAILURE;
    }
    GElf_Ehdr ehdr;
    if (gelf_getehdr(elf, &ehdr) == NULL)
    {
        fprintf(stderr, "gelf_getehdr() failed\n");
        elf_end(elf);
        close(fd);
        return EXIT_FAILURE;
    }
    uint8_t address_size = (ehdr.e_ident[EI_CLASS] == ELFCLASS64) ? 8 : 4;
    size_t shstrndx;
    if (elf_getshdrstrndx(elf, &shstrndx) != 0)
    {
        fprintf(stderr, "elf_getshdrstrndx() failed\n");
        elf_end(elf);
        close(fd);
        return EXIT_FAILURE;
    }
    Elf_Scn *scn = NULL;
    const uint8_t *debug_line_data = NULL;
    size_t debug_line_size = 0;
    while ((scn = elf_nextscn(elf, scn)) != NULL)
    {
        GElf_Shdr shdr;
        if (gelf_getshdr(scn, &shdr) != &shdr)
            continue;
        const char *name = elf_strptr(elf, shstrndx, shdr.sh_name);
        if (name && strcmp(name, ".debug_line") == 0)
        {
            Elf_Data *data_section = elf_getdata(scn, NULL);
            if (data_section)
            {
                debug_line_data = data_section->d_buf;
                debug_line_size = data_section->d_size;
            }
            break;
        }
    }
    if (!debug_line_data)
    {
        fprintf(stderr, ".debug_line section not found\n");
        elf_end(elf);
        close(fd);
        return EXIT_FAILURE;
    }
    puts("Processing...");
    process_debug_line_section_v4(debug_line_data, debug_line_size, address_size);
    elf_end(elf);
    close(fd);
    return EXIT_SUCCESS;
}
