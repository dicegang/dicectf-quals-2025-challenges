/* tslint:disable */
/* eslint-disable */
/**
* You should call this once to ensure that if the compiler crashes it gets
* reported in JavaScript.
* @param {boolean} debug
*/
export function initialise_panic_hook(debug: boolean): void;
/**
* Reset the virtual file system to an empty state.
* @param {number} project_id
*/
export function reset_filesystem(project_id: number): void;
/**
* Delete project, freeing any memory associated with it.
* @param {number} project_id
*/
export function delete_project(project_id: number): void;
/**
* Write a Gleam module to the `/src` directory of the virtual file system.
* @param {number} project_id
* @param {string} module_name
* @param {string} code
*/
export function write_module(project_id: number, module_name: string, code: string): void;
/**
* Write a file to the virtual file system.
* @param {number} project_id
* @param {string} path
* @param {string} content
*/
export function write_file(project_id: number, path: string, content: string): void;
/**
* Write a non-text file to the virtual file system.
* @param {number} project_id
* @param {string} path
* @param {Uint8Array} content
*/
export function write_file_bytes(project_id: number, path: string, content: Uint8Array): void;
/**
* Read a file from the virtual file system.
* @param {number} project_id
* @param {string} path
* @returns {Uint8Array | undefined}
*/
export function read_file_bytes(project_id: number, path: string): Uint8Array | undefined;
/**
* Run the package compiler. If this succeeds you can use
* @param {number} project_id
* @param {string} target
*/
export function compile_package(project_id: number, target: string): void;
/**
* Get the compiled JavaScript output for a given module.
*
* You need to call `compile_package` before calling this function.
* @param {number} project_id
* @param {string} module_name
* @returns {string | undefined}
*/
export function read_compiled_javascript(project_id: number, module_name: string): string | undefined;
/**
* Get the compiled Erlang output for a given module.
*
* You need to call `compile_package` before calling this function.
* @param {number} project_id
* @param {string} module_name
* @returns {string | undefined}
*/
export function read_compiled_erlang(project_id: number, module_name: string): string | undefined;
/**
* Clear any stored warnings. This is performed automatically when before compilation.
* @param {number} project_id
*/
export function reset_warnings(project_id: number): void;
/**
* Pop the latest warning from the compiler.
* @param {number} project_id
* @returns {string | undefined}
*/
export function pop_warning(project_id: number): string | undefined;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
  readonly memory: WebAssembly.Memory;
  readonly initialise_panic_hook: (a: number) => void;
  readonly delete_project: (a: number) => void;
  readonly write_module: (a: number, b: number, c: number, d: number, e: number) => void;
  readonly write_file: (a: number, b: number, c: number, d: number, e: number) => void;
  readonly write_file_bytes: (a: number, b: number, c: number, d: number, e: number) => void;
  readonly read_file_bytes: (a: number, b: number, c: number, d: number) => void;
  readonly compile_package: (a: number, b: number, c: number, d: number) => void;
  readonly read_compiled_javascript: (a: number, b: number, c: number, d: number) => void;
  readonly read_compiled_erlang: (a: number, b: number, c: number, d: number) => void;
  readonly pop_warning: (a: number, b: number) => void;
  readonly reset_filesystem: (a: number) => void;
  readonly reset_warnings: (a: number) => void;
  readonly ring_core_0_17_8_bn_mul_mont: (a: number, b: number, c: number, d: number, e: number, f: number) => void;
  readonly __wbindgen_malloc: (a: number, b: number) => number;
  readonly __wbindgen_realloc: (a: number, b: number, c: number, d: number) => number;
  readonly __wbindgen_add_to_stack_pointer: (a: number) => number;
  readonly __wbindgen_free: (a: number, b: number, c: number) => void;
  readonly __wbindgen_exn_store: (a: number) => void;
}

export type SyncInitInput = BufferSource | WebAssembly.Module;
/**
* Instantiates the given `module`, which can either be bytes or
* a precompiled `WebAssembly.Module`.
*
* @param {{ module: SyncInitInput }} module - Passing `SyncInitInput` directly is deprecated.
*
* @returns {InitOutput}
*/
export function initSync(module: { module: SyncInitInput } | SyncInitInput): InitOutput;

/**
* If `module_or_path` is {RequestInfo} or {URL}, makes a request and
* for everything else, calls `WebAssembly.instantiate` directly.
*
* @param {{ module_or_path: InitInput | Promise<InitInput> }} module_or_path - Passing `InitInput` directly is deprecated.
*
* @returns {Promise<InitOutput>}
*/
export default function __wbg_init (module_or_path?: { module_or_path: InitInput | Promise<InitInput> } | InitInput | Promise<InitInput>): Promise<InitOutput>;
