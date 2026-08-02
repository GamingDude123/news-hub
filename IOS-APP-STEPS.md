# Turning EcoTrace into an iPhone app

Plain-English steps. You do not need to rewrite the app. You wrap the file you
already have inside a real iOS app using a tool called **Capacitor**.

Words used here:

- **Terminal** — the black window where you type commands. Open it with Cmd+Space, type "Terminal", press Enter.
- **Xcode** — Apple's free program for building iPhone apps.
- **Capacitor** — the wrapper that puts your web page inside a real app.
- **Bundle ID** — a unique name for your app, written backwards, like `com.jack.ecotrace`.

## Which device do I do this on?

**Nearly all of it is on the Mac.** Xcode does not exist for iPhone, so you
cannot start any of this on your phone.

| Steps | Do it on |
| --- | --- |
| 1 to 16 | Mac |
| 17 | Phone — plug it into the Mac, tap Trust |
| 18 | Mac — press the play button |
| 19 | Phone — Settings, to trust yourself as a developer |
| Later changes | Mac |

Sit at the Mac. Keep your phone and its cable nearby. You will not touch the
phone until Step 17.

---

## Part 1 — Install the tools (once)

### Step 1. Install Xcode

Open the App Store on your Mac. Search **Xcode**. Click Get / Install.
It is about 7 GB, so this takes a while. Let it finish before moving on.

### Step 2. Open Xcode once

Open Xcode. It will ask to install extra parts. Say yes. Agree to the licence.
Then close it.

### Step 3. Tell your Mac to use Xcode's tools

In Terminal, paste this and press Enter. It will ask for your Mac password:

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

### Step 4. Check that Node is installed

Node lets you run the Capacitor commands. In Terminal:

```bash
node -v
```

If you see a version number like `v20.11.0`, you are fine. If you see
"command not found", download Node from https://nodejs.org (pick the LTS
button), install it, then close and reopen Terminal.

---

## Part 2 — Build the app project (once)

### Step 5. Make a new folder for the app

```bash
mkdir -p ~/Projects/ecotrace-app/www
```

### Step 6. Copy your HTML in, renamed to index.html

The app must find a file called `index.html`, so we rename it as we copy:

```bash
cp ~/Projects/news-hub/ecotrace.html ~/Projects/ecotrace-app/www/index.html
```

### Step 7. Go into the new folder

```bash
cd ~/Projects/ecotrace-app
```

Stay in this folder for every command below.

### Step 8. Start a Node project

```bash
npm init -y
```

### Step 9. Install Capacitor

```bash
npm install @capacitor/core @capacitor/cli @capacitor/ios
```

### Step 10. Set up Capacitor

```bash
npx cap init EcoTrace com.yourname.ecotrace --web-dir=www
```

Change `com.yourname.ecotrace` to your own name, for example
`com.jackbenherz.ecotrace`. Use only letters and dots. No spaces, no numbers
at the start of a part.

### Step 11. Add the iPhone version

```bash
npx cap add ios
```

This creates an `ios` folder. That folder is a real Xcode project.

---

## Part 3 — Let the app use the camera

Apple blocks the camera unless you write down a reason for it.

### Step 12. Open the settings file

```bash
open -a Xcode ~/Projects/ecotrace-app/ios/App/App/Info.plist
```

### Step 13. Add the camera permission

In Xcode, hover over any row in that list and click the small **+** button.
A new row appears with a dropdown.

- In the left box, type: `Privacy - Camera Usage Description`
- In the right box (Value), type: `EcoTrace uses the camera to scan barcodes.`

Press Cmd+S to save.

That sentence is what your phone shows in the permission popup, so write
something a normal person would understand.

---

## Part 4 — Put it on your iPhone

### Step 14. Open the project in Xcode

```bash
npx cap open ios
```

### Step 15. Sign in with your Apple ID

In Xcode's menu bar: **Xcode → Settings → Accounts**. Click **+**, choose
**Apple ID**, sign in with your normal Apple account. A free account works.

### Step 16. Choose your signing team

In the left sidebar of Xcode, click the blue **App** icon at the top.
In the middle, click the **Signing & Capabilities** tab.

- Tick **Automatically manage signing**
- In **Team**, pick your name (it will say "Personal Team")

If it shows a red error about the bundle ID being taken, change the
**Bundle Identifier** box slightly, for example add `2` on the end.

### Step 17. Plug in your iPhone

Connect it with a cable. On the phone, tap **Trust** if asked.

At the top of the Xcode window there is a dropdown that probably says
"iPhone 15 Simulator". Click it and pick **your actual iPhone** from the list.

> The Simulator is a fake iPhone on your screen. It has no camera, so barcode
> scanning will not work there. Use your real phone.

### Step 18. Press Run

Click the ▶︎ play button at the top left of Xcode. Wait. The app installs
onto your phone and opens.

### Step 19. Trust yourself on the phone

The first time, the phone refuses to open the app. Fix it on the phone:

**Settings → General → VPN & Device Management → your Apple ID → Trust**

Now open EcoTrace from your home screen. Tap **Open camera**, allow the
permission, and point it at any barcode.

---

## Part 5 — Making changes later

Every time you edit `ecotrace.html`, do these three commands:

```bash
cp ~/Projects/news-hub/ecotrace.html ~/Projects/ecotrace-app/www/index.html
```

```bash
cd ~/Projects/ecotrace-app && npx cap sync ios
```

Then press ▶︎ in Xcode again.

---

## Things that will trip you up

**The app dies after 7 days.** With a free Apple account, apps you install
yourself stop working after one week. Just press ▶︎ in Xcode again to
reinstall. Paying the $99/year Apple Developer fee removes this limit.

**The app needs internet the first time it scans.** iPhone Safari cannot
decode barcodes on its own, so the app downloads a small decoder called
ZXing from the internet. After the first successful scan it is cached, but
a first run with no signal will fail. To fix this properly, see below.

**The camera only works on a real phone**, never the Simulator.

---

## Optional — make scanning work offline and better

Two ways, pick one.

### Easy way: download the decoder into the app

```bash
cd ~/Projects/ecotrace-app && npm install zxing-wasm
```

```bash
mkdir -p www/vendor && cp -r node_modules/zxing-wasm/dist www/vendor/zxing
```

Then in `www/index.html`, find this line:

```js
const ZXING_URL = "https://cdn.jsdelivr.net/npm/zxing-wasm@2/+esm";
```

and change it to:

```js
const ZXING_URL = "./vendor/zxing/es/index.js";
```

Do the same for the font: delete the two `<link>` lines near the top that
point at `fonts.googleapis.com`. The app will use the iPhone's own system
font instead, which honestly looks fine.

### Better way: use Apple and Google's own scanner

This is faster and much better at reading bent, shiny or badly lit barcodes,
because it uses Google's ML Kit instead of a web decoder.

```bash
cd ~/Projects/ecotrace-app && npm install @capacitor-mlkit/barcode-scanning && npx cap sync ios
```

Then the JavaScript changes: instead of opening the camera yourself, you call
the plugin and it hands you back a barcode string. That is a real code change
rather than a copy-paste, so do it once the wrapper above is already working.

---

## Putting it on the App Store

Only worth doing when the app is finished.

1. Pay $99/year at https://developer.apple.com/programs
2. In Xcode, set the dropdown at the top to **Any iOS Device**
3. Menu bar: **Product → Archive**
4. When it finishes, click **Distribute App → App Store Connect**
5. Go to https://appstoreconnect.apple.com, create the app listing, add
   screenshots, a description and a privacy label
6. Submit for review. Apple usually replies within 1–3 days

One warning for this app specifically: Apple rejects apps that make claims
about real companies without evidence. The demo data is invented and the
brands are fictional, which is fine for a portfolio piece — but you must not
ship invented labour-abuse claims about real brands.
