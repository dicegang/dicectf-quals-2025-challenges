# Solving

tl;dr patching or intercepting a network request to enable hidden behaviour.

For each 'video' loaded, a request is sent to `api.thecatapi.com`; an image URL is loaded from the response, then the image is rendered to the terminal.

There is hidden behaviour where if the field `dice` is set with the value `"gang"`, a static embedded image with the flag is loaded and displayed instead.

To solve, we can either patch this branch, or run a `catapi.com` [proxy](./solve/).

Run the proxy (`cargo b -p solve && sudo ./target/debug/solve`), point `api.thecatapi.com` to `localhost` in /etc/hosts, then run dicetok
