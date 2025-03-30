# debugalyzer

tl;dr flag checker added to DWARF opcodes.

## Analysis
We're given a binary `dwarf` and small binary `main` which prints 'Debug me!'. `dwarf` is a modified DWARF4 data parser with some added opcodes.

```c
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
```
`set_flag` takes a uleb128 followed by a single byte, and stores the byte at that offset into the global bytearray `flag`.

```c
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
                    flag_ok = 0;
                }

                break;
            }
```

`check_flag` takes 2 uleb128 offsets, followed by an 'op' byte an an 'expected' byte. If `flag[off1] <OP> flag[off2] != expected`, then `flag_ok` is set to `false`.

## Flag Checker

The `main` binary repeats `set_flag` and initializes the flag to `dice{XXXXX...XXXX}`. There are then a series of checks. We can solve by parsing the binary, extracting the checks, then using Z3 to solve them. This is implemented in [`solve`](./solve/).

To verify the flag, we can patch the flag into the `set_flag` operations. This is implemented by running [`solve_rev`](./gen_elf/src/bin/solve_rev.rs).
