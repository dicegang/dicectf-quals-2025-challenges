#!/usr/bin/env bun
import init, * as wasm from './gleam/gleam_wasm.js'

void (async () => {
    const lines = [prompt('>>> ')]
    while (lines.at(-1)) lines.push(prompt('>>> '))
    const program = lines.join('\n')

    if (program.includes('import')) return console.log('no imports')
    if (program.includes('@')) return console.log('no externals')

    await init({})

    wasm.initialise_panic_hook();
    wasm.write_module(0, 'mod', program);
    wasm.compile_package(0, 'javascript')

    const compiled = wasm.read_compiled_javascript(0, 'mod')
    const blob = new Blob([compiled], { type: 'application/javascript' })
    const url = URL.createObjectURL(blob)
    const module = await import(url)

    if (module.main) console.log(module.main())
    else console.log('nothing to do')
})()
