# eoink28.github.io

My personal website. A 16-bit version of me stands in a little game window, and as you scroll the camera moves down through him: the brain for projects, the mouth for what I talk about, the heart for what I love and the legs for getting outdoors. After that there's a pixel map of everywhere I've travelled, with a world view and a closer Europe view. A Writing page holds reports and research papers.

Live at **https://eoink28.github.io**

## How it's built

Plain HTML, CSS and JavaScript. No framework and no build step for the page itself.

- **No cookies, analytics or third-party requests.** The font is hosted here too, so nothing loads from Google or anywhere else. The only thing stored is the light/dark choice, in the visitor's own browser. `privacy.html` explains it.
- **HTTPS only.** GitHub Pages serves the site over HTTPS, and every page has a Content Security Policy that only allows files from this site.
- **Light and dark mode.** Follows the device setting until the visitor presses the switch.
- **Respects reduced motion.** If a device asks for less motion, the animations stop and the camera cuts instead of gliding.
- **Works without JavaScript.** You lose the camera moves and the map, but every section still reads.

```
index.html                 the page
writing/index.html         reports and research papers
writing/files/             PDFs for the writing page (create it when you add the first one)
privacy.html               privacy and cookies notice
404.html                   not found page (GitHub Pages uses it automatically)
assets/css/site.css        all styling, including the camera positions for each body part
assets/js/theme-init.js    applies light/dark before the page paints
assets/js/site.js          theme switch, body tour, card pop-ups, travel map
assets/js/travel.js        the list of countries I've been to (edit this)
assets/js/world-pixels.js  the map grid (generated)
assets/fonts/              Archivo, under the SIL Open Font License
assets/img/                favicon, touch icon, link preview image
assets/cv/                 the CV PDF (currently a placeholder)
tools/                     scripts that generate the pixel art, map and images
```

## Run it locally

```bash
python3 -m http.server 8787
```

Then open http://localhost:8787.

## Common edits

**Replace the CV.** Save the real one over `assets/cv/Eoin-Kenny-CV.pdf`, keeping the name. All the download buttons point at it.

**Add a report or paper.** Open `writing/index.html`, copy the example block inside the comment in the list, fill it in and move it outside the comment (newest first). Use `data-type="paper"` for a research paper or `data-type="report"` for a report, and put the PDF in `writing/files/`. The "First ones on the way" card and the filter buttons switch themselves over once there's at least one entry.

**Add a country.** Add a line to `assets/js/travel.js`. If the map calls the country something different, add `map:` with the map's name (point at the country on the map to see it), like the USA already does. A country is counted once however many lines point at it. Add `note:` for a second line under the label, like the UK has.

**Change the words.** Everything is in `index.html`, one `<section>` per body part. Then run the writing check:

```bash
python3 tools/check_writing.py
```

It fails on em and en dashes, curly quotes, emoji and wording that commonly reads as AI-written. The same check runs on GitHub on every push.

**After changing anything in `assets/`.** Stamp the new version onto the links so nobody's browser serves an old copy:

```bash
python3 tools/version_assets.py
```

**Change the pixel art.** The character, the brain, heart, speech bubble, mountains and icons are text grids in `tools/build_pixels.py`, one character per pixel. Edit a grid, then run:

```bash
python3 tools/build_pixels.py
```

It rewrites the art inside the `<!-- px:name -->` blocks in the HTML and regenerates the favicon.

**Rebuild the map.** Only needed if you change the map views or resolution (the `VIEWS` list at the top of the script), or which overseas territories are kept apart from their mainland (`HOME`). Download `countries-50m.json` from the [world-atlas](https://www.npmjs.com/package/world-atlas) package (Natural Earth data, public domain), then:

```bash
python3 tools/build_map.py path/to/countries-50m.json
```

## Putting it online

The repository has to be called exactly `eoink28.github.io` for GitHub to serve it at that address.

```bash
cd ~/Personal/projects/eoink28.github.io
git init -b main
git add .
git status
git commit -m "Personal website"
gh repo create eoink28.github.io --public --source=. --push
```

Then on GitHub, go to **Settings > Pages**, choose **Deploy from a branch**, branch `main`, folder `/ (root)`, and make sure **Enforce HTTPS** is ticked. After that, every `git push` updates the site.

## Adding a custom domain later

eoinkenny.com is taken. On 14 September 2026, eoinkenny.dev, .me, .io and .net were all free. `.dev` is a good pick because every browser forces HTTPS on it.

1. Buy the domain (Cloudflare, Porkbun and Namecheap all sell `.dev`).
2. Add these DNS records at the registrar:
   - `A` records for `@`: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `AAAA` records for `@`: `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`
   - `CNAME` for `www`: `eoink28.github.io`
3. On GitHub, go to **Settings > Pages > Custom domain**, enter the domain and save. Tick **Enforce HTTPS** once the certificate is ready.
4. Swap the addresses across the site and write the CNAME file, then commit and push:

```bash
./tools/set_domain.sh eoinkenny.ie
```

GitHub redirects the old address to the new domain, so existing links keep working.

To go back to the github.io address later (for example if the domain isn't renewed), run `./tools/set_domain.sh eoink28.github.io`, push, and clear the custom domain in **Settings > Pages**. Do that *before* the domain expires, so the site never redirects to a name someone else owns.

## The link preview image

`assets/img/og.png` is what LinkedIn shows when the link is shared. It's a screenshot of `tools/og.html`. With the local server running:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --hide-scrollbars --window-size=1200,630 --virtual-time-budget=3000 --screenshot="$PWD/assets/img/og.png" http://127.0.0.1:8787/tools/og.html
```

LinkedIn caches previews. After changing the image, paste the URL into the [LinkedIn Post Inspector](https://www.linkedin.com/post-inspector/) to refresh it.
