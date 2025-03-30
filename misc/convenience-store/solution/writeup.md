# convenience store (dicectf2025)

**Category**: misc/web/android

**Authors**: orion, hpmv

* [Android Studio](https://developer.android.com/studio) is recommended

## files

`web-src.zip` is distributed with the challenge and consists of:
 * A Python Flask web application, including static JavaScript resources and Flask template files
 * A `docker-compose.yml` file to run the web application for local testing.
 * `instructions.md` is also a separate Markdown file with more details on how to submit an Android app solution and the judging process.

The challenge description mentions the flag matches the regex `dice\{[a-z0-9]{10,20}\}`.

## observations


### The web app

The distributed files provides the source for a Python Flask web app lets users store, view and search for notes. 

From `/`, a user can login/register a new account by logging in with new credentials.

The `/notes` endpoint provides an interface to create a new note, and also displays a list of the user's notes underneath.

The `/search` endpoint allows users to query for an existing note. The query is part of the URL query parameter (i.e. `/search?query=<your query>`). If there exists a note matching the query in the user's notes, a result will be returned which consists of a note image (that is included as an embedded Base64-encoded icon in the page).

For those who are familiar with the genre - this web app is a classic 'note storage' app that is ~~blatantly ripped of~~ inspired by [FBCTF 2019's Secret Note Keeper challenge](https://ctftime.org/task/8659) (hopefully giving some hint that this is an [XS-Leaks](https://xsleaks.dev/) challenge).


### Static files
The provided static JavaScript files used in the web app are all the official minified bundles for Bootstrap, JQuery and Popper with [Subresource Integrity (SRI)](https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity) and hashes that match their official documentation. There isn't intended to be anything sketchy to attack here.

### Cookies
The web app is enforcing some [security on cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies). `SameSite=Lax` is set, which means the cookie is only sent cross-origin for top-level navigations (e.g. by clicking on a link or navigating with the URL bar). `HttpOnly=True` is also set as an additional defense against XSS, which means that the cookie values cannot be accessed by JavaScript code.

### Caching
The web app sets a bunch of headers to avoid responses being cached (`Cache-Control`, `Pragma` and `Expires`). 

(The `/search` page returns a page with a hilariously large base64-embedded image...perhaps something timing-related is relevant here?)

### Framing protections
[Framing protections](https://xsleaks.dev/docs/defenses/opt-in/xfo/) are set, with `frame-ancesctors` set to `none` and [`X-Frame-Options`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Frame-Options) is set to `DENY` to prevent the site from being embdedded from attacker origins.

This, in conjection with `SameSite=Lax` HTTP cookies indicates that the site intends to be accessed via top-level navigation only.

### Content Security Policy
The rest of the web app's CSP apart from `frame-ancestors` is [quite restrictive](https://csp-evaluator.withgoogle.com/). `script-src` allows only the same hashes used in SRI for the Bootstrap, JQuery and Popper frameworks, rather than a vulnerable configuration based on URL allowlists, and this configuration also does not allow untrusted inline scripts or `javascript:` URLS. `base-uri` is restricted to block the injection of `<base>` tags, preventing attackers from changing the locations of scripts loaded from relative URLs. `object-src` is also restricted to disable dangerous plugins like Flash. 

(This CSP configuration, in addition with `HttpOnly` cookies, strongly tries to hint that XSS is not the intended exploitation path here.)


## solution
### Challenge setup
This challenge is based on a vulnerability discussed in this paper: [_The Bridge between Web Applications and Mobile Platforms is Still Broken (Beer, 2022)_](https://minimalblue.com/data/papers/SECWEB22_broken_bridge.pdf)

In the setup of the challenge, the notes app is available at `10.2.2.2:8000`. There exists an admin who is logged into this notes application on their Android phone (using Chrome). Within their notes, there exists a note that contains the value of the flag.

The attacker's goal is to steal the contents of this secret note one character at a time via an XS-Leaks attack (since the `HttpOnly` and CSP settings means we can't steal admin's cookie and login as them to get the secret note) We are also given that the flag matches the regex `dice\{[a-z0-9]{10,20}\}` in the challenge description, which narrows down the search space.


### Android Custom Tabs
[Android Custom Tabs](https://developer.chrome.com/docs/android/custom-tabs) are a feature of Android browsers that allow native app developers to add web content to their app. It provides a middle-ground between launching an external browser (disruptive context switch) and WebView (very primitive environment that doesn't support many web features and shares no state with the browser).

The key idea here is **custom tabs shares state** (i.e. cookies). If a user is logged into `trustedsite.com` on their preferred Android browser (say, Chrome) and a random 3P Android application `UntrustedApp` opens a Chrome Custom Tab - the user will automatically be logged in on that site, since the tab behaves as if it were a regular tab of the web browser.

This by itself isn't really a problem, however the 3P Android app is able to receive some information about the page loaded in the Custom Tab via [navigation signals](https://developer.chrome.com/docs/android/custom-tabs/guide-engagement-signals).

This setup is identical to an untrusted 3P site iframing the trusted site - however, in this case setting `frame-ancestors` in CSP and `X-Frame-Options` will not help, since this is a top level navigation in a mobile app. Hello, XS-Leaks!

### Solving
**tl;dr:**
1. Admin is logged in on the notes web app (`10.2.2.2:8000`) in Chrome.
2. Attacker crafts a malicious Android app that launches [Chrome Custom Tabs](https://developer.chrome.com/docs/android/custom-tabs/guide-engagement-signals).
3. Admin is also automatically logged into the notes web app with their cookies in the Custom Tab.
4. The attacker app can perform an XS-Leaks attack by [timing navigation events](https://developer.chrome.com/docs/android/custom-tabs/guide-engagement-signals) from the web app running in the Custom Tab with their malicious app.

The solution is to craft an attacker app that does the following:
1. Bind to Chrome's [Custom Tabs service](https://developer.chrome.com/docs/android/custom-tabs/guide-engagement-signals) using `CustomTabsServiceConnection`
2. Create a session with [`CustomTabsCallback` to monitor navigation timing events](https://developer.chrome.com/docs/android/custom-tabs/guide-engagement-signals) looking at the difference between `CustomTabsCallback.NAVIGATION_STARTED` and `CustomTabsCallback.NAVIGATION_FINISHED`.
3. Repeatedly launch `10.2.2.2:8000/search?query=<known flag part>` starting with the known prefix `dice{...}`, iterating through each allowed character in the search space (`[a-z0-9\{\}]`), to brute force the next character of the flag. The correct next character is the one with the longest load time, since successful searches will return a large base64-encoded embedded image in the page, while unsuccessful searches will not.
4. Stop when the last character of the flag is found (i.e. `}`)


> Note: The judging environment does **not** have external web access and will not be able to access any domains other than the notes app that is hosted on `10.2.2.2:8000`. With the intended exploitation path, it is not necessary to access any other sites other than this.

Note that since the attacker app only gets to run for 30 seconds on the judging infrastructure, only a few characters of the flag can be recovered with the first attempt. It's necessary to then modify the attacker app to start searching with the newly identified flag prefix, recompile this new app, submit it again to continue searching and so on until the full flag is retrieved (or guessed, lol).

> **Challenge author note:** Unfortunately, even without the artifical execution limit it seems that the attacker app will freeze and stop responding after a certain number of flag characters are retrieved. I am not sure if this is due to some limitation on the number of requests that can be made concurrently in Custom Tabs, but we thought it would be slightly less confusing to have this execution limit to force people to resubmit apps rather than have them run into this strange behavior.

A sample solution solution is provided in the `AttackerApp` directory of this repostiroy. Additionally, in the `/apks` folder of this repository, all 3 APKs used to retrieve parts of the flag (and eventually the whole flag), along with the corresponding logcat output from the judge is included.

## Infrastructure

The judging infrastructure for this challenge is very similar to [spellbound (347 points)](https://github.com/dicegang/dicectf-quals-2024-challenges/tree/main/misc/spellbound) from [DiceCTF 2024 Quals](https://github.com/dicegang/dicectf-quals-2024-challenges/tree/main).

It was hosted externally and is not included in the source code here. Contact hpmv or orion if you are interested in the infrastructure setup.
