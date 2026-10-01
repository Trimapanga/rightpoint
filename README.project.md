# Right Point Solutions - Django site

An improved rebuild of rightpoint.co.ke as a Django 5 project: server-rendered
marketing pages for a Nairobi security technology company, with a content admin,
a working enquiry pipeline, structured data and an importable content seed.

The previous site was a client-rendered React build, so crawlers received mostly
schema metadata and there was no way for the team to edit copy, publish a product
or capture an enquiry without a code change. This version puts content in the
database, renders it on the server, and keeps the visual language of the original.

## Quick start

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed            # load real solutions, catalogue and references
python manage.py createsuperuser
python manage.py runserver
```

Then open http://127.0.0.1:8000/ and http://127.0.0.1:8000/admin/.

Set `DJANGO_DB_ENGINE` and friends in the environment to use Postgres instead of
the default SQLite file. Copy `.env.example` for the full list of settings.

## Layout

| Path | Purpose |
| --- | --- |
| `config/` | Settings, root URLconf, WSGI/ASGI entry points |
| `core/` | `SiteSetting` singleton, context processor (nav, partner marks, reference tiles), home/about, error pages, robots, sitemap, `seed` command |
| `solutions/` | Capabilities (CCTV, access control, fencing, data centres, consultancy, assessments) with process steps and why-points |
| `products/` | Brand and category facets, the product catalogue and the session-backed quote list (`basket.py`) |
| `casestudies/` | Reference profiles |
| `contact/` | Enquiry form, spam handling, stored inquiries, admin triage |
| `templates/` | All page templates and reusable partials |
| `static/` | Design system (`css/site.css`), behaviour (`js/site.js`), icons |

## Brand assets

`static/img/logo.png` is the supplied RPS wordmark with the white background
knocked out to transparency and trimmed. Colours are sampled from it:
blue `#023AAA` and green `#2B990B`. The theme is light, so the artwork sits
directly on the page and both brand colours pass WCAG AA as text
(`--accent: #1e7a08` at 5.5:1, `--blue-bright: #0b57c2` at 6.7:1 on white).
Palette lives in the `:root` block of `static/css/site.css`. The tab icons are derived from the
same file by `tools/make_favicon.py`: it drops the "Right Point Solutions" wordmark (mush at 16px,
and the tab title already spells it out), keeps the ring-and-RPS mark, and sits it on a white
plate because iOS paints transparency black. `favicon-32.png`, `favicon-192.png` and
`apple-touch-icon.png` are checked in rather than generated at build time, so re-run the tool
after any change to `logo.png`.

## Page patterns

### The page ground is paper, not white

`--bg` is `#f5f7f5` and `--bg-elev` is `#eef1ee` - a cool green-neutral paper in the same
family as the brand marks, not a stark white and not a grey. Pure white is reserved for
*things*: `--surface`, the card gradients' top stop, `.chip`, `.logo-plate`, form inputs and
the footer's brand tile. That is what gives the page its depth ladder (band `#e9ece9` ->
ground `#f5f7f5` -> plate `#ffffff`) and why a white plate now visibly lifts off the page by
a 1.0766:1 luminance step where it used to sit flush at 1.00. Everything tinted in the sheet
was re-derived for the new ground: the hero and banner washes dropped to `0.12/0.13/0.07` and
`0.11/0.11` so they read as light on paper instead of stains on white, the sticky header is
`rgba(255,255,255,.92)` glass (the one chrome surface that is genuinely white, because it sits
over everything and has to read as a slab, not a band), each card's
bottom stop moved off the old blue-grays (`#fafcfc`) to the paper family (`#f9fbf8`,
`#f4f7f3`, `#f7faf6`, `#f6faf6`), and `<meta name="theme-color">` follows `--bg`.

The contrast floors are narrower now that the ground is darker, so check them before
deepening any band further. Measured against the deepest stop in the sheet (`#e9ece9`):
`--text` 14.76, `--muted` 5.63, `--accent` **4.59**, `--muted-dim` **4.71**, `--brand-blue`
8.06. `--accent` and `--muted-dim` have under 0.15:1 of headroom there - do not darken
`--bg-elev`'s end stop again, and do not use a tone lighter than `--accent` for text on a band.

`static/img/hero-crew-cut.webp` (plus a 640px variant for `srcset`) is the
supplied crew poster with its white backdrop knocked out to transparency, so it
sits directly on the page instead of as a white block. The alpha ramps between
luminance 205 and 245 rather than cutting off hard, which avoids white fringing
around the lettering. `static/img/hero-crew.jpg` keeps the opaque version and is
the default `og:image`, since social cards render transparency unpredictably.

`static/img/clients/` holds the reference marks for the home page logo wall, named after the
case study slug they resolve against: `elimu-sacco.png` (from the elimusacco.com site header),
`synthesis-kenya.png` (synthesis.co.ke `/images/logo.png`, whose baked-in 50%-alpha white
rectangle was knocked back to transparency with PIL - no artwork cropped) and
`fincom-africa.png` (fincomafrica.com's own header logo) and `ibs-bank-somalia.png`
(ibsbank.so's header lockup, the same 2058x554 file Wikimedia hosts as "IBS bank logo
2019.png" - the bank crops its own canvas flush against the wordmark, so the copy was
padded 4% on every side rather than trimmed). All four are transparent PNGs; none of
those sites publishes an SVG. Teetop Shop has no bundled mark - its domain is a parked
page now and the original store never served a logo image, so the wall falls back to the
typeset wordmark rather than inventing one. Quest Group is a wordmark for the same
reason: no Kenyan commercial property company by that name could be identified online
(`quest.co.ke` is a liquor store), so its mark needs to come from the client.

`static/img/solutions/` holds the two supplied renders: a live-wire perimeter crew
(`electric-fencing.webp`) and a dome-camera close-up cropped out of the `rightpoint.co.ke`
poster (`cctv-video-intelligence.webp`, named for the solution slug it resolves against).
They are generated artwork rather than site photography, so `image_caption` stays
descriptive of what is depicted and never claims a real installation. The full poster is
not published: its location line reads "Poços de Caldas, Minas Gerais", which is not where
the company works.

The hero and footer were designed as a pair, each carrying a gradient hairline and a masked
grid motif; **the hero's grid is now removed** (`hero::before` deleted on 2026-09-29), so the
hero keeps only its three brand washes over the `#fafcf9 -> --bg` ramp plus the closing hairline,
while the footer keeps both. The masked grid motif now reads on the ink surfaces - the capability
band, the reference tiles' art panel, the footer's lower half - which is where it has the
contrast to be seen; on the near-white hero it was 1px `--line` rules at `opacity: 0.5`. The
technician cutout sits on a halo with a blurred contact shadow so it reads as art rather than a
pasted image. The numbered capability row that used to sit under the buttons (`solutions|slice:":4"`
as `.hero-chips`) was cut on 2026-09-30 - the hero is now heading, lede and the two buttons only;
see "Dead rules kept on purpose" for what stayed behind to restore it.

**The hero is a full-height band** (`min-height: 100vh` then `100svh`, `display: grid` +
`align-content: center`), so the copy centres in the viewport instead of hugging the top. Two
things to know before changing it. The chrome above is *in flow* - the 44px utility bar plus the
64px sticky header - so at scroll 0 the hero begins at y=108 and its last 108px sit below the
fold; subtract `calc(var(--topbar-h) + var(--header-h))` from the `min-height` if the first
screen should end
exactly at the fold. And the grid makes the mobile `figure.hero-visual` a second row (measured at
the 0-width viewport: hero 1131px, shell 782 + figure 221); with a taller box `align-content`
centres that pair as one block, verified by pinning `min-height: 1400px` - the content group sat
207px below the hero's top edge and 190.5px above its bottom edge, i.e. the 269px of free space
split evenly inside the 72/56px padding.

`site.hero_kicker` ("Security, engineered for reality") is **no longer printed**: the `<p class="kicker">`
came out of the hero on 2026-09-30, leaving `site.hero_heading` as the page's only `h1`. The
`SiteSetting` field, its admin row and the `.hero .kicker` glass-pill rules all stay so restoring
it is one template line - see "Dead rules kept on purpose".

### The home body: a capability index, then a reference rail

Home now runs hero -> logo wall -> `#capabilities` -> `#equipment` -> `#references` -> footer. The two bands no
longer share a scale: `#capabilities` turned into the page's ink chapter (rebuilt 2026-09-30) and
took `padding-block: clamp(3.2rem, 7vw, 5.6rem)` - 89.6px at 1200px - while `#references` kept the
compact `clamp(2.6rem, 5.4vw, 4.2rem)`. Ink and paper still alternate rather than stack: one ink
band, one paper rail. Measured in a 1200px layout the bands are 862px and 772px tall; at a 510px
viewport they are 892px and 717px, and no descendant of the ink band crosses its shell's content
box (`max(right edge) - shell right = 0`).

`#references` is no longer home's property: it lives in `templates/partials/reference_band.html`
and `base.html` includes it between `</main>` and the equipment strip, so every page closes on
proof rather than only the home page. `clients` therefore moved out of `HomeView` into
`core.context_processors.site` (with `.only(...)` limited to the fields a tile reads plus the two
`Meta.ordering` keys the queryset sorts on: `slug`,
`client`, `sector`, `country`, `eyebrow`, `image`, `published_on`, `order`). Two consequences: `templates/casestudies/list.html`
overrides `{% block reference_band %}` empty, because that page *is* the list and printing the same
profiles twice on one screen is silly; and the band can now land directly under another
`.section-alt` (it does on `/products/`, `/solutions/`, `/about/` and both case-study pages), whose
gradient ends at `#e9ece9` against the band's `#eef1ee` start - a ~5/255 step, invisible - so
`main:has(> .section-alt:last-child) + .reference-band { border-block-start: 0 }` leaves exactly one
1px rule at the seam instead of two stacked. Measured both ways: `/products/` neighbour border-bottom
1px + band border-top 0px, `/contact/` neighbour 0px + band 1px.

`#capabilities` is one ink chapter, not a console object: `.capability-band` paints the surface
(`#0b2530 -> #0a1e28 52% -> #071820` under a 42% blue bloom at `88%/6%` and a 30% green one at
`2%/96%`), and `::before`/`::after` add the lit arrival rule and the masked `--grid` motif, so the
index sits straight on it. Text tones were composited through the same stack in sRGB - CSS
gradients default to `color-interpolation-method: srgb`, and blending in linear light inflates a
dark ground badly (it once reported 4:1 for white against a surface that measures 10.8:1): the
green bloom's core is the worst ground, `#123e1a` at luminance 0.0373, where white measures **12.03:1**, the `rgba(255,255,255,.66)` descriptors **6.33:1** and a
`--brand-green-lift` numeral **6.41:1**; the `rgba(.55)` numeral on the plain base is the only tone
under 6:1 at **5.03:1**, and it brightens to `--brand-green-lift` on hover. The plate is the one
light surface in the band, so its text is `--text`/`--muted-dim` on `#fff -> #eef1ee`.

`.capability-split` puts the copy on `minmax(0, 1.06fr)` and the object on `0.94fr` with a
`clamp(2rem, 5vw, 4.5rem)` gap - 555px and 508px at 1200px - because a row is a term and a
descriptor side by side and both want to stay on one line. `.capability-lead` then stacks the
intro, the index and the `.capability-foot` rail in one column so every hairline runs the full
measure. The rows are `grid-template-columns: auto minmax(0, 1.05fr) minmax(0, 1fr) auto` with
`align-items: baseline`, so the numeral, the term and the descriptor share a baseline and the
descriptor column starts at the same x in every row (240px and 229px at 1200px). `min-height: 68px`
plus `align-content: center` is what makes the six rows one rhythm: four of the six descriptors
wrap to a second line at that measure, so without the floor the rail alternates 49px and 67px rows
and stops reading as a table. Separators are real 1px `rgba(255,255,255,.12)` borders - `border-top`
per row and `border-bottom` on `:last-child` - because nothing here is rounded any more; the old
inset box-shadow existed to stop a border squaring off the console's 12px row radius. The
hover/focus accent is still the 2px brand bar growing down the leading edge, and the row's numeral
picks up `--brand-green-lift` with it.

The row descriptor is **`Solution.tagline`**, a property that returns the summary's first sentence
("A smart perimeter is your first line of defence."), because the full 145-159 character summary
cannot hold one line next to a 1.45rem term. `HomeBodyTests` asserts `tagline`, not `summary`; the
whole summary still prints on the solution detail page.

Right of the index sits `.capability-orbit`, the band's one object: two concentric rings, a masked
conic sweep rotating around the inner one (`orbit-sweep`, 26s, stopped by the global
`prefers-reduced-motion` rule), three chips on the outer ring - `Design`, `Install`, `Support`, the
same three words `templates/core/about.html` and `templates/solutions/detail.html` already use -
and a light plate at the centre listing the handover pack ("As-built drawings / IP plans /
Credential registers / Training records", the list `about.html` prints as "Documented handover").
The figure is `aspect-ratio: 1 / 1` at `max-width: 460px` so the rings stay circles (460x460, plate
292x259 centred at 84,100, chips landing at r=204-208 against a 207px ring), and it is deliberately
`display: block`: **absolutely positioned children of a grid container resolve their percentage
offsets against a grid area and `place-items` shifts them too** - with `place-items: center` the
chip asked for at `left: 76%` measured 90%. On a block box the ring coordinates are exact, and the
plate is centred with the `top/left: 50%` + `translate(-50%,-50%)` idiom for the same reason. The
chips overhang the figure by ~16px on the left, which lands in the 72px column gap, not outside the
shell.

`.capability-orbit` is `role="img"` with an `aria-label` and `aria-hidden` inside, so the object
reads as one sentence instead of a fragmentary list, and it drops out below 640px (a 292px plate
with chips reaching past it does not fit a phone column). Between 860px and 1039px `.split` stacks
and the object narrows to 380px (band height 1311px in a 900px shell, no overflow); below 860px the
row gives up its side-by-side descriptor and puts it on a second grid row under the term.

**The band assembles on arrival** rather than appearing whole. The intro and the count rail take
the generic `rise`; the six rows wipe in from the leading edge on a 70ms cascade
(`capability-row-in`, `--row-delay` per `:nth-child`, 0-350ms) because they are a sequence and
should enter like one; the object scales up behind its own rings (`capability-orbit-in`), then the
three chips pop (`satellite-in`, 0.52/0.64/0.76s) and the handover lines tick in under it. Two
details worth knowing before editing. `satellite-in` carries the `translate(-50%,-50%)` through
every step - the chips are centred by a transform, so a keyframe that animated `scale` alone would
drop them onto their top-left corner. And the delayed ones need `animation-fill-mode: backwards`:
the moment `.is-visible` lands, the `:not(.is-visible)` parked state stops matching, so without a
backwards fill a row would sit fully visible until its wait expired. Nothing uses `forwards`, so a
finished entrance never outranks the hover transforms above it. The satellites and plate lines are
keyed off the *figure's* `.is-visible`, not their own, so they wait for the object instead of the
page. Verified by forcing `.is-visible` and finishing each animation: rows and foot land at
`opacity: 1 / transform: none`, a chip lands at `opacity: 1` with its `matrix(1,0,0,1,-39.9,-15.1)`
centre offset intact. (In the 0-width probe tab `.capability-orbit` is `display: none` under the
640px rule, so its subtree reports a frozen `opacity: 0` until the figure is forced to render - an
artefact of the harness, not of the sheet.) The reduced-motion block restates the parked states at
the band's own class-chain specificity and zeroes the delays, because a `0.001ms` duration still
runs *in delay order* and would otherwise leave the plate's lines blank until each wait expired.

`#references` is a full-bleed right-to-left rail, not a card grid. `.reference-rail` deliberately
sits *outside* `.shell` so the tiles run to the viewport edges, and its `mask-image` (transparent
to black at 6%, black to transparent at 94% - the opaque band is 72px..1128px at 1200px) does the
fading the shell's padding used to imply; four of the six tiles are inside it there, two at 510px.

Each `.reference-tile` is built as an **image card**: `padding: 0` so the `.reference-media` art
panel bleeds to the 1px border (measured 0.0px of inset on all four axes), and a caption that is
`position: absolute; inset: auto 0 0` floating over the panel's lower edge rather than a block
stacked under it. Tiles are `flex: 0 0 clamp(252px, 25vw, 296px)` at
`min-height: clamp(268px, 28vw, 312px)` - 296x312 at 1200px, 252x268 at 510px - and because the
caption takes no flow height the panel is always the full 294x310 and every tile's art area stays
identical even when a client name wraps. The panel is lit the way a photograph is: key light at
`50%/-14%`, brand rim lights in the two lower corners, the `--grid` motif masked to the top light.
The photographic work itself (top highlight, bottom vignette, hairline inner frame) is
`.reference-media::before` at `z-index: 3`, deliberately *above* `.reference-img`, so the same
light falls on a client's uploaded photograph as on the painted panel - and the panel is what
renders today, because `{% if study.image %}` is false for every profile so far.

**A photograph drops straight into the shape.** `CaseStudy.image` (admin "Media" fieldset,
`upload_to="case-studies/"`, served by `static(MEDIA_URL, ...)` in `config/urls.py`) renders as
`.reference-img`: `position: absolute; inset: 0`, `width/height: 100%`, `object-fit: cover`. A
1600x400 test card was measured filling the 294x310 panel to 0.0px on every side with the mark
chip still floating over it and the caption's bottom edge sitting exactly on the art's, so no
further CSS change is needed to make the rail photographic. `alt` stays empty: the client's name
is printed on the tile directly under the art, so a non-empty alt would read the same thing twice.
**The lit mark chip is not optional** - every supplied client logo is dark or mid-tone on
transparency and would vanish against this ink, and the `{{ study.client }}` wordmark fallback is
`--text` too, so both sit on a `#fff -> #e9eff4 78% -> #dfe8ef` chip (218x84px at 1200px, mark
contained at 42px; the widest mark, Fincom, renders 180.4px inside a 182.8px content box, which is
why the cap is `max-width: 100%` and not a fixed px - a wider file letterboxes instead of
distorting; wordmark on the chip's darkest stop measures 14.17:1). The caption scrim is
`linear-gradient(to top, rgba(4,10,13,.97), rgba(4,10,13,.88) 50%, rgba(4,10,13,.58) 78%,
transparent)`, held dense across the text rows because it will one day float over artwork I do not
control: rasterised against the painted panel the ground runs 0.0030-0.0191 luminance and the
three tones measure name `#ffffff` 19.54:1, `--brand-green-lift` index 10.22:1,
`rgba(255,255,255,.66)` scope 8.66:1 - and against a *blown-out white photograph*, the worst case
a client could upload, they still clear AA at 15.59 / 5.63 / 8.03:1.

The loop is the same two-group `translateX(-50%)` trick as the logo walls, and it needed one
correction that only measurement catches: `gap` only puts gutters *between* items, so the clone's
first tile originally butted flush against group one's last - a 0px seam in a 20.4px rhythm,
reading as a clap once per cycle. `.reference-group` therefore carries a `padding-inline-end`
equal to its `gap`, which makes each group exactly `tiles x (tile + gutter)` wide (1898.4px at
1200px, 1593.6px at 510px), keeps every gutter including the seam at one value, and leaves
`-50%` landing on precisely one group (measured delta 0.0). `min-width: 100vw` on the group is
what still covers a wide screen when the table is short.

`partials/reference_slides.html` is included twice, the second pass with `clone=True`, which makes
that group `aria-hidden` and gives all six of its links `tabindex="-1"` - `HomeBodyTests` asserts
nothing in the real group carries `tabindex` and everything after the clone does. Hover and focus
pause the track (the tiles are links), and `prefers-reduced-motion` drops the animation, removes
the clone from flow, drops the mask and turns the rail into an `overflow-x: auto` snap row, so a
stopped loop never hides a profile.

Both bands are wrapped in `{% if solutions %}` / `{% if clients %}` so an empty table can never
print a heading with nothing under it. `.capability-count` is
`{{ solutions|length|stringformat:"02d" }}` and `HomeBodyTests` asserts the printed count equals
the number of rows - which is why the `h2` states a property ("Designed, installed and handed
over as one system.") instead of naming six disciplines: the headline would otherwise go stale
the moment a register is unpublished. The rail's `.reference-scope` prints
`sector|default:eyebrow` then `country`, and the ` &middot; ` separator only renders when **both**
are present: Teetop Shop has an empty `sector`, so an unconditional separator printed a leading
"· Kenya". The `.split` collapse in the `max-width: 1040px` block sits later in the sheet than
`.capability-split`, so it wins at equal specificity and the band stacks on phones and tablets;
if the sheet order ever changes, restate it.

### The home shelf band (`#equipment`)

The band under the capability index puts hardware on the front page without duplicating the
shop: `HomeView` supplies `shelf` (the seven featured lines in curated order), `stock_count`
and `shelf_departments` (the five groups with published product, busiest first). The first line
becomes a wide panel - plate at 86%, eyebrow, summary, the first four `spec_table` rows and both
actions - and the remaining six reuse `partials/product_card.html` unchanged, so the basket
context processor, the AJAX add and the "On your list" flag work from the home page exactly as
they do in the shop. The panel is not a `.product-card`, so it carries its own two
`.is-on-list` rules. Three cards per row, one feature panel per band: `is_featured` is the only
curation switch, and nothing here prints a price or an invented figure.

### The region band ("Our services go beyond Kenya")

Below the shelf, `templates/core/home.html` closes the page with the countries the firm works
in: Kenya as the base card, then Uganda, Tanzania, Somalia, Sudan, Rwanda and Ethiopia. The list
lives in `core.views.SERVICE_REGIONS` (code, name, and a `role` only Kenya carries) and is passed
as `service_regions`; the view resolves each mark through `static()` so a hashed manifest storage
still gets a real URL. Kenya is the heavier card on purpose - ink well, green ring, larger mark,
"Headquarters" in mono - so the band reads as one base plus a reach, not seven equal.

**The marks are drawn, not emoji.** The band originally used regional-indicator pairs
(`🇰🇪`), which Windows and most server Linux font stacks render as two bare letters - "KE", "UG" -
inside the circle. `python tools/generate_region_flags.py` redraws all seven as 96px circular
SVGs (`static/img/flags/<iso>.svg`): real stripe geometry, the Rwandan sun and Ethiopian pentagram
built from trig, and hand-simplified emblems for the Kenya shield-and-spears and the Ugandan
crowned crane, which are the two that must still read at 68px. National flags are public symbols,
but these files are our own artwork like every other plate in the repository.
`core.tests.HomeRegionTests` fails if a listed country has no flag file, or if the band ever
goes back to emoji.

### /products/ is a shop with an enquiry basket, not a till

The catalogue page borrows retail *chrome* - department tiles, a sticky refine rail, a sort
bar, a dense shelf grid, flags on the cards - but nothing in it may imply a transaction the
site cannot honour. There are **no prices, no stock counts, no delivery promises and no
invented numbers**: every UI fact comes from a real column. Sorting is a five-key whitelist
(`views.SORTS`: curated `order`, name A-Z / Z-A, manufacturer, product group), the department
tiles print annotated `product_count`s, `is_featured` is the "Curated pick" flag, the card's
three bullets are the first three rows of `spec_table()`, and the rail states outright why
the shelf has no prices. The primary action adds to a **quote list**, and that list ends in
the existing spam-guarded enquiry form rather than a checkout.

Imagery obeys the same rule: every card carries a schematic plate of the device's form factor,
drawn here, never a vendor press shot or a generated image of a product that may not exist in
that finish. The plate is decorative (`aria-hidden` on its frame, empty `alt` on the art) - the
card's facts are the eyebrow, title and the three specification rows.

The list itself is `products/basket.py`: session-only, so there is no model and no migration
to keep in sync if a product is unpublished. Keys are `str(pk)`, quantities are whole numbers
1-99, a list holds at most 30 lines, and rows keep insertion order. `raw()` re-coerces the
stored map on every read because a session is user-reachable data, and `lines()` drops rows
whose product has gone unpublished *without* rewriting the session - a stale session can
therefore not 500 a page, and a test asserts both behaviours.

Two shapes matter for editing it:

- **Every control is a form, and the JS only upgrades it.** Add, +/-, remove and clear are real
  `{% csrf_token %}` POSTs that redirect back to `next` (only `/`-prefixed paths are accepted, so
  an off-site `next` falls back to the basket page). `site.js` delegates one `submit` handler, and
  an `X-Requested-With: XMLHttpRequest` request gets `basket_fragment()` JSON
  (`count, distinct, slugs, html, empty_html, isEmpty`) instead of a redirect. That single payload
  repaints the drawer, the basket page's own copy of the row list and the header badge, so adding a
  control needs no new JavaScript. Mutations answer 405 to GET and a bad fragment POST answers 400
  with `{error}` - never a redirect, which would render the message as a page.
- **`basket/` must stay registered *before* `<slug:slug>/`** in `products/urls.py`: "basket" is a
  valid slug, so the detail route would otherwise win and every basket URL would 404.

`products.context_processors.basket_summary` puts `basket_rows`, `basket_count` and
`basket_slugs` on every page so the list survives navigation; it returns empty lists without
touching the ORM when the session holds nothing (asserted: 0 queries empty, 1 filled).
Shelf cards get `is-on-list` and `data-basket-slug` from `basket_slugs`, which is what the
fragment handler toggles in place. The card's buy row needs
`.product-card .add-form, .product-card .btn-link { position: relative; z-index: 2 }` because
`.link-card a::after` lays a full-card click overlay at `z-index: 1` and the generic rescue at
`site.css:312` only matches anchors, not forms. `.dept-tile.is-active` is the one ink plate in
the shop, and the drawer is `z-index: 95` with the flash stack deliberately raised to 98 above
it, so a rejected quantity is still readable over an open list. `.shop-rail` sticks at
`top: calc(var(--header-h) + 1.1rem)` - it depends on `--header-h` matching the real bar, so see
the primary-nav measurement above before touching either.

### Dead rules kept on purpose

`#solutions`, `#why`, `.solution-bento`, `.services-visual`, `.why-rail` and
`static/img/services-flyer-cut.webp` have **no markup anywhere in `templates/`** - the bands
were cut from `home.html` in an earlier pass. The same is true of the reference dossier set
(`.ref-lead`, `.ref-in`, `.ref-copy`, `.ref-mark`, `.ref-logo`, `.ref-stamp`, `.ref-points`,
`.ref-source`, `.ref-word`): `#references` was rebuilt as a sliding rail and those rules were
left behind rather than deleted. And so is the footer's trust bar (`.footer-badges-bar`,
`.footer-badge-item`, `.badge-icon-box`, `.badge-text-box`, `.badge-title`, `.badge-desc`): cut from
`footer.html` on 2026-09-29 along with its four claims (licensed & insured, audited as-built
handover, SLA support, Tier-1 OEM integration) - copy the marketing team may well ask back, and it
costs nothing but sheet length. Those rules and the flyer artwork stay in place because this
project is not under version control and a prune is unrecoverable. The footer's pre-footer CTA
console is a different case: cut from `templates/partials/footer.html` on 2026-09-29 (first its copy
column - `.footer-cta-content`, `.footer-kicker`, `.footer-status-pill`, `.status-radar` +
`@keyframes radar-pulse`, `.footer-meta-item`, `.footer-kicker-dot`, `.footer-motto`,
`.footer-submotto`, `.footer-cta-highlights`, `.footer-cta-chip` - then the rest of it:
`.footer-cta-card`, `.footer-cta-group`, `.footer-cta-btn`, `.footer-quick-phone`,
`.quick-phone-icon`, `.quick-phone-text`, `.footer-cta-guarantee`), and it took its CSS with it. The
markup was declarative copy and three action links that a rebuild would re-argue rather than
re-print, so nothing of it is left in the sheet. Same again on 2026-09-30, when `#capabilities`
became an ink band: `.capability-console`, `.capability-console-label` and `.capability-text`
went with the console markup they existed for. Kept for the opposite reason: `.hero .kicker` and
`.hero .kicker::before` (the glass pill and its lit dot), which lost their only markup on
2026-09-30 when the hero kicker line was deleted but the `SiteSetting.hero_kicker` field, its
default and its admin row all stayed live. Treat anything documented
below those passages as history, not as a live guarantee, and check a section exists in a
template before styling or describing it.

The hero's capability row is the same kind of keep. Its markup went on 2026-09-30, and what is
left is the whole restore path in one place: `.hero-chips` and its four rules (the `07 ·`
`counter-increment: hero-cap` prefix, the transition set and `.is-current`'s brand-gradient
lift) in the sheet, and the `[data-count-rotate]` walker in `site.js` that steps `.is-current`
through the chips every 1.9s, pauses on hover/focus and stands down under
`prefers-reduced-motion`. That JS is now the only live code with no markup to run against -
`querySelector` returns null and the block no-ops - so re-adding the `{% if solutions %}` nav
to `home.html` brings the animation back without touching a line of it.

`.footer-wordmark` is the same again from the footer: its `<p class="shell footer-wordmark">` came
out of `partials/footer.html` on 2026-09-30, and the sheet keeps the rule, its
`@supports (background-clip: text)` gradient and its entry in the
`.footer-grid, .footer-wordmark, .footer-bottom, .footer-badges-bar { z-index: 1 }` group. The text
was never copy - it is `{{ site.company_name }}`, live in the admin and printed again in the
copyright line - so one template line restores the watermark and nothing about it would have to be
re-argued.

The footer is the page's closing statement, not a link dump. Its ink is a base ramp
(`#07152b -> #040e1f -> #020710`) under four radials - blue key lights at 20%/-8% and 98%/95%,
a green rim at 85%/-6% and a deep blue floor at 2%/102% - every one centred *off* canvas, plus a
gradient hairline and a masked grid motif on the lower half. Rasterising that stack over a
1200px-wide surface puts the brightest ground pixel at `rgb(13,45,44)` (luminance 0.0214). The
figures below were measured against the console's 6% white glass as well (luminance 0.0351, the
brightest ground this sheet ever had); with that glass cut the ink is darker everywhere, so every
ratio quoted here is now a **conservative lower bound** rather than the exact value. It is still
the floor for
every tone chosen here: white at `.85/.78/.72/.68/.65` measures 9.21/7.94/6.95/6.33/5.89:1, and
`--blue-lift`/`--brand-green-lift` clear 5.09/6.57:1. **No white label may go below `0.58` alpha**
- `0.5` measured 4.00:1 and `0.52` only 4.56:1 at that worst pixel, which is why the mono labels
(`.contact-card-tag`, `.hours-label`,
`.footer-legal`) sit at `0.58-0.6` and `.badge-desc`/`.contact-card-sub` at `0.55` - the badge class
is dead markup now, but its alpha was part of that sweep. `--muted`,
`--muted-dim` and `--accent` cannot appear on this ink at all; heading rules, contact icons and
the maps link take `--brand-green-lift`.

Structure, top to bottom: `.footer-grid`
is a 1.35fr + 1fr + 0.95fr + 1.35fr directory whose cells carry a 1px left rule so the four columns
read as one spec sheet
(the rules and pads come back out below 1041px, where the grid wraps to two columns);
the four-item trust bar (`.footer-badges-bar` - licensed/insured, as-built handover, SLA support,
OEM integration) was cut from `footer.html` on 2026-09-29 and the `site.company_name`
`background-clip: text` watermark (`.footer-wordmark`) on 2026-09-30, so the footer goes
directory -> bottom bar;
`.footer-bottom` closes with the copyright, the datasheet note, a systems-status pill and
back-to-top.

**It is deliberately compact** (2026-09-29): the directory and
bottom bar all run one scale tighter than their first cut -
body 0.8-0.84rem, labels 0.62-0.7rem, directory
padding-block `clamp(1.5rem, 3vw, 2.2rem) / clamp(1.2rem, 2.4vw, 1.6rem)`, icon squares 26-30px,
the brand disc 92px. Keep the *ratios* when resizing: the ladder is
body > label > micro, and the size cut must not take a footer link below the 24px WCAG
2.5.8 target minimum (`.footer-list` gap is 0.35rem with 0.15rem link padding for that reason).
The CTA console is gone (2026-09-29), so the footer *opens* on the directory and `.site-footer`'s
`padding-top` took over the job the console's `margin-block-start` used to do:
`clamp(1.6rem, 3.5vw, 2.4rem)` - 42.4px on desktop, 25.6px at the floor - sitting under the 1px
`::before` hairline, which is absolutely positioned so padding never moves it. Measured with the
shell pinned to 1200px and each footer `vw` clamp resolved to its own 1200px value: the first
directory content lands **79.4px** below the top edge (42.4 pad + the grid's 1px `border-top` +
its 36px pad), the four columns are 300.1 / 222.3 / 211.2 / 300.1px across 1120px with 28.8px
gutters, and the footer is **621.4px** tall (directory 445.7, bottom bar 133.4, plus the
`padding-top` above them - the 75.6px watermark band that used to sit between the two is gone).
Stacked at 510px it measures **1336.7px** (single 469.2px column: directory 1177.7, bottom bar
133.4) - the clamps are all at their floors by 510px, but the *width*
still has to be pinned, because `vw` resolves against this probe's 0px viewport. Both totals are
the 2026-09-29 pass minus its own recorded band figure, so treat them as derived: re-inserting
`.footer-wordmark` and resolving its clamps to their 1200px values measures 83.2px, not 75.6px,
which is the drift to re-check if these numbers ever matter.
`padding-top` used to be `1px` and was load-bearing in exactly one way - it stopped the
console's top margin collapsing out of the unpadded `.shell` wrapper - so keep a real value here
unless something else owns that gap. Nothing overflows horizontally any more (`scrollWidth` equals
the shell at 1200px); the old 533-vs-474.8 overflow was the console's clipped `::before` glow.

Three consequences worth knowing before editing: `.footer-brand .brand-plate` is a **round
badge** - a 92px disc, `border-radius: 50%`, coin highlight (`radial-gradient(78% 78% at 30%
22%, #ffffff, #e9eff6 74%, #dfe7f1)`) and a 5px halo ring - because `logo.png` is `#023aaa` on
transparency and would vanish on navy. The wordmark is `width: 68%` of the disc, which keeps its
1.63:1 aspect untouched and puts its 73.5px diagonal inside the 92px circle with 18px of
clearance, so the badge is round *around* the artwork instead of clipping it (never crop the
supplied logo). Specificity: `.footer-brand .brand-plate .brand-logo` is three classes, which is
what beats `.brand-plate-lg .brand-logo { height: 52px }`, and the plate rules sit far below
`.brand-plate:hover` in the sheet so the hover can't repaint the border with `--line-strong`.
It is a link to the home page (the Company column repeats it as a text entry, and the primary
nav opens with Home); `.footer-contact a` needs `max-width: 100%`
*with* `overflow-wrap: anywhere`, because an inline-flex link sizes to max-content and the
unbroken e-mail address walked out of its 200px column between 1041px and about 1250px until it
was capped; and `.footer-wordmark` (dead markup now, see below) also carried `.shell`, so its
`margin` is `0 auto` rather
than `0` - the reset shorthand would drop the centring and park a full-width line at the left
edge.

Surface depth lives in four tokens at the top of `static/css/site.css` - `--shadow-soft`,
`--shadow-lift`, `--edge` (the inset top highlight) and `--grad-brand` - which every
raised element reuses: cards, steps, pillars, panes, pills and pagination. Hovering a
card fades in a `::before` bloom, so `.card > :not(.link-card)`
holds the child stacking; the `.link-card` title must stay unpositioned or the
whole-card click overlay breaks. Scroll reveals are keyframe-based (`.rise`) rather
than transition-based because a `transition` on `.reveal` would override each
component's own hover timing. The observer's target list lives in `site.js`
(`.card, .pillar, .panel, .step, .capability-intro, .capability-row, .capability-orbit,
.capability-foot, .reveal`) and it is what adds the `reveal` class - so an element that is not
listed never hides, and with JavaScript off nothing is listed, which is the safe failure mode. `.section-head p` is a deliberately blunt rule that styles
every intro paragraph in a section header, so `.section-head .kicker` has to restate the
label's own size and colour - without it the mono kicker inherits the 1.05rem grey intro
styling and reads as a second paragraph.

The primary nav (`templates/partials/header.html`) opens with **Home**, then the Solutions
submenu, Products, Case studies, About and Contact, and Home is the only entry that carries
`is-active` from `request.path == '/'`. Because the wordmark plate is `aria-label`ed rather
than read as text, a text route home in the nav is what a keyboard and screen-reader user
actually gets.

The bar's grammar came from `techashi.shiva.co.ke` on 2026-09-30: a glass slab
(`rgba(255,255,255,.92)` over `blur(16px) saturate(1.5)`, a 1px `rgba(13,33,40,.09)` hairline
and a wide soft lift plus a tight contact shadow), 64px tall, with the links as quiet text -
`0.845rem`, weight 400, colour-only hover, no fills - and the quote-list control as a 40px
round icon plate whose count badge rides the corner. Two departures are deliberate. The active
page keeps a 2px `--brand-green` underline at a 7px offset, because a nav with no fill state
otherwise loses its orientation cue. And the brand column stays the supplied `logo.png` alone:
their mark + stacked two-line wordmark would print our name twice (the artwork already carries
it) and cost ~150px of row width. The phone number dropped from a ghost button to a plain
`.nav-phone` text line so "Secure your site" is the only solid thing on the bar.

`--header-h` is now the single source of truth for everything that has to clear the chrome:
the mobile drawer's `inset: var(--header-h) 0 auto` and `max-height`, `.shop-rail`'s `top`, and
the flash-stack's `top`. The drawer lands flush under the bar at any scroll position because
`backdrop-filter` makes the header a containing block for its own `position: fixed` descendants,
so `inset` measures from the header's padding box rather than the viewport. The badge needs the
explicit `.basket-badge[hidden] { display: none }` guard - `display: inline-grid` on the class
outranks the UA rule for the `hidden` attribute the JS sets on an empty list.

The row declares no `flex-wrap`, so it defaults to `nowrap` and `.brand` owns the slack with
`margin-right: auto`; its width is therefore measured rather than assumed. With every child
forced to `width: auto`: brand 75 + nav 691 + control 40 + two 18.4px gaps = **843px**, against
a shell of 920px at a 1000px viewport, 1020px at 1100px and 1120px from 1200px up
(`clamp(1.1rem, 4vw, 2.5rem)` side padding against the 1200px cap). Thinnest measured slack is
**+77px at 1000px**, which is why the `1000-1199px` step-down block the pill nav needed is gone -
one breakpoint, the drawer taking over at **999px**, above which the row is only brand + Menu +
control. Re-measure before adding a seventh entry or a third CTA. Over-budget still does not
show as horizontal overflow: `white-space: nowrap` on `.nav-link` is the safety, so a label that
cannot fit wraps the *text* and inflates the bar past `--header-h`, silently mis-stating every
offset listed above.

The home page's "Why Right Point" band is a snap rail rather than a grid (`.why-rail` /
`.why-card`): native `overflow-x` plus `scroll-snap-type: x mandatory` does all the
sliding, so swipe and keyboard work with no script at all. `site.js` only decorates it -
the two arrow buttons, the `01 / 04` read-out, the `--rail-frac` / `--rail-pos` meter and
the disabled ends - and hides both when the cards already fit. There is no auto-advance
on purpose: rotating content the user did not ask for is a WCAG 2.2.2 trap, and a rail
that moves by itself defeats a tap. The band keeps its light textured surface (`#why`
adds two brand washes and the masked grid motif the footer uses) while the rail
sits in an **ink console** (`.why-console`), so the depth ladder is light band to ink well
to lifted glass cards and the section head never has to be re-coloured. That is also why
`--brand-green-lift` and `--blue-lift` exist: `--brand-green` is only 4.7:1 on ink, and
`--grad-brand` too dark for the meter to read against its track. The rail's own padding is
not decoration - a scroll container clips on both axes, so it is the only room a lifted
card and its shadow have. `.why-card` is deliberately not in the reveal observer's list,
since cards sitting off-rail would never intersect and would stay at `opacity: 0`.
`.pillar` / `.pillars` are untouched because `core/about.html` and
`contact/thank_you.html` still use that grid.

## Content model

Everything the marketing team needs to change lives in the admin:

- **Site settings** (singleton) - company name, hero copy, phone, WhatsApp, email, `working_hours`, address, about text. Hours and location also drive the utility bar above the nav (`templates/partials/topbar.html`), which scrolls away while the sticky header stays; `--topbar-h` keeps the fixed flash-stack clear of it at the top of a page.
- **Solutions** - one per capability, with an icon, chips, deliverables, outcomes and ordered process steps. Multi-line text fields render as bullet lists. `Solution.image_src` mirrors `CaseStudy.logo_src`: an admin upload first, then artwork bundled at `static/img/solutions/<slug>.<webp|png|jpg|svg>`, then nothing. Rasters are tried before SVG on purpose: the supplied flyer artwork and the generated poster share a slug and the photograph of the real installation wins. The two accessors are not the same thing, because the two surfaces crop differently - `Solution.image_is_photo` is true only for a raster, and the card (`.sol-plate`, which fills itself `cover`-style behind the copy) uses it, while `image_src` also returns the drawn vertical posters and the detail page's `.deliver-visual` backdrop uses that. A 900x1200 poster behind body text would be sliced to rib; a flyer photograph is what the card wants. With no raster the plate keeps its dark ink gradient and the icon badge, so a card is never empty. The artwork's main home is still the detail page, where it is a framed figure on phones and the right-hand backdrop of the "What we deliver" section from desktop up (`.deliver-visual`, masked where the copy ends). On the home page a capability is one row of the `#capabilities` index - numeral, title and `Solution.tagline` (the summary's first sentence) - not a card; the `.solution-bento` rules that used to hold those cards are dead markup, listed under "Dead rules kept on purpose".
  The four capabilities that had no artwork are covered by `python tools/generate_solution_posters.py`, hand-drawn vector plates in the house ink language (`access-control`, `data-centre-construction`, `security-risk-consultancy`, `security-assessments`) plus three site graphics (`img/site/one-system.svg`, `coverage-nairobi.svg`, `not-found.svg`). The capability posters are **900x1200 verticals, not 4:3**: `.deliver-visual` is a 47%-wide strip running the full height of the section with `object-fit: cover`, and `figure.frame img` on phones is a 4/3 cover window, so a landscape poster was sliced down the middle of the subject. Every poster therefore stands its subject on the horizon at `0.70 * height` and crosses the 16:9 card band (the `.sol-plate` window) with something recognisable. `solutions.tests.SolutionTests.test_every_seeded_solution_ships_artwork` fails if seed data and posters drift apart. `not-found.svg` is the mark on the custom 404 page (`.error-visual`, styled in `site.css` because `error_base.html` loads that sheet only); `one-system.svg` and `coverage-nairobi.svg` are currently unreferenced - inner-page heroes were asked to stay image-free.
- **Products** - brand, category, `Label: value` feature lines (rendered as a specification table), datasheet link, featured flag. `Product.image_src` follows the same ladder as `Brand.logo_src`: an admin upload, then bundled artwork at `static/img/products/<slug>.<webp|svg>`, then nothing (`.jpg` is deliberately absent - see the catalogue-import note below) - and the card falls through to the brand monogram, so a product with no artwork is never a hole in the grid. Two kinds of bundled artwork exist and the template must know which it got, so `Product.image_is_photo` says whether the resolved file is a photograph (`.webp`) or a drawing (`.svg`): a photograph renders full-bleed as `img.card-media`, a plate keeps the `.product-visual` well with the line drawing centred inside it. Six of the 26 products are photographs today (the Evolis Primacy 2 and Zenius 2 printers, the YMCKO ribbon pack, the IDEMIA SIGMA family, and ZKTeco's two walk-through arches); the other twenty are **our own schematic line drawings** - 320×200 transparent-ground elevations in ink `#0d1b20` with the two brand accents, on the CSS gradient plate - because we hold no rights to vendor press imagery and an invented product photo would be a claim about a device we have never photographed.
  The photo tiles come from `python tools/prepare_product_photos.py`. It accepts any photograph in `images/` named after a live product slug (`images/hikvision-colorvu.jpg` - the expected route, since distributor media kits are licensed to resellers), plus the eight short-named files the 2026-09-30 import left behind, mapped by hand. `--check` lists the slugs still waiting; `images/README.md` is the same list with what each shot has to show. Each accepted file is written to `static/img/products/<slug>.webp` at **960×600 - the same 16/10 window the card and the shelf feature use** - with the background lifted off the near-white scan, the product trimmed, scaled to fit a 7% margin and centred. It never touches the source files. Two products are refused by the gate: `hikvision-minmoe` and `idemia-visionpass` arrive as branded artwork with a coloured surround, and `plain_surrounds` (plus a 340px minimum on the source subject's longest edge) keeps them on their schematic plate rather than shipping a vendor graphic we have not cleared. **That photography has no reuse licence** - see the catalogue-import note below - so these tiles are bundled for the draft, not cleared for publication. `products.tests.ProductArtworkTests.test_every_seeded_product_ships_a_plate` fails if seed data and plates drift apart, and `test_only_checked_photography_is_published` pins the published tile set to a hand-verified list, because a filename is not a description of a picture.
  Re-draw the plates with `python tools/generate_product_plates.py` - the script is the source of the artwork, the files in `static/img/products/` are its output.
- **Brands** - name, one-line speciality and logo upload. They appear in the sliding mark row above the footer on every page, linked to that brand's filtered catalogue; without a logo the entry falls back to a lettered monogram. `Brand.logo_src` prefers the upload, then a bundled `static/img/brands/<slug>.svg|.png`, then nothing. ZKTeco has no bundled mark, so it renders as "ZK". The row is the client wall's marquee pattern copied exactly (`partials/brand_strip.html` + `partials/brand_logos.html` with a `clone=True` second pass), and the circular plates are gone: bare marks, because eight identical tiles said more about the layout than about the equipment. One trap in `width: auto` marks that lazy-load: an unloaded image resolves to zero width and collapses its slot, so `.brand-item img` reserves `min-width` and lets `object-fit: contain` keep the ratio.

Bundled marks are third-party trademarked artwork: IDEMIA and Evolis came from the
vendors' own sites, Hikvision and Entrust from Wikimedia Commons. The IDEMIA file
ships white (`fill: #fff`) for dark backgrounds and was recoloured to `#0d1b20` for
the light strip. Confirm the right to publish each logo with the client before going live.
- **Case studies** - situation / approach / outcome plus verifiable public reference links.
  The home page also publishes them as a logo wall under the hero
  (`templates/partials/client_strip.html`): bare marks on the band, no cards, drifting
  right to left. `CaseStudy.logo_src` mirrors `Brand.logo_src`: uploaded artwork, then a
  bundled `static/img/clients/<slug>.svg|.png`, then the client name typeset as a
  wordmark, so a missing logo never leaves a gap. Upload artwork in the admin or drop
  files in that folder - names are only listed with the client's permission.
  The loop is CSS only: `.client-track` holds two identical groups, each forced to
  `min-width: 100vw`, and slides `translateX(-50%)`, so the copy lands exactly where the
  first began and the wrap never shows a seam. `partials/client_logos.html` is included
  twice, the second time with `clone=True`, which makes that group `aria-hidden` and its
  links `tabindex="-1"` so assistive tech and the tab order meet each reference once.
  Hover and keyboard focus pause the slide (they are links, not decoration) and
  `prefers-reduced-motion` stops it outright.
  The `#references` band reuses the same loop at tile scale
  (`templates/partials/reference_slides.html`, included twice with the second pass `clone=True`):
  each tile links the profile and prints only what identifies it - `image` as the bleeding
  artwork when a profile has one, `logo_src` mark or typeset wordmark on the lit chip, `client`,
  and `sector|default:eyebrow` with `country`. No date, no "Public record" pill, no `highlights`
  lines and **no invented photography**: the art slot is filled from the admin or it shows the lit
  panel, because generated artwork over a real customer's name would imply an installation at
  their site that never happened. The full record - situation, approach, outcome, verifiable
  public source - stays on the case-study page itself. That rail is no longer home-only:
  `base.html` includes `partials/reference_band.html` above the equipment strip, so every page
  closes on proof, `/case-studies/` opts out with an empty `{% block reference_band %}` rather
  than repeat itself, and `clients` comes from `context_processors.site()` instead of `HomeView`.
- **Contact inquiries** - every submission with status workflow and bulk actions.

`python manage.py seed` upserts the current real content, so it is safe to re-run
after editing `core/management/commands/seed.py`. It currently loads 5 brands, 8 product
categories and 26 products. Every catalogue row is a publicly named product *family* from a
brand the site already lists - no model numbers, no datasheet URLs and no specification that
was not published by the manufacturer. Where a datasheet link would have to be guessed,
`datasheet_url` stays empty and the template hides the link. Adding a product means adding its
plate to `static/img/products/` too; `ProductArtworkTests` keeps the two in step and refuses a
seed row whose slug or title repeats.

That repeat check exists because of the 2026-09-30 catalogue import, which appended a second copy
of eight products under short slugs (`primacy`, `ribbon`, `cards`, `sigma`, `minmoe`,
`hik-readers`, `walkthrough`, `quantum`), a second `idemia-visionpass` row, four one-off categories
and a placeholder brand called "Security". `update_or_create(slug=...)` meant the later row silently
won, so the richer entries were the ones deleted - the seed and the dev database are now back to
26 distinct products. The same import dropped roughly 1.2MB of manufacturer photography into
`static/img/products/` under those dead short slugs. **Those files are still there and no reuse
licence was established for them.** They stay unreachable through `image_src` (the ladder only
tries `<slug>.webp` and `<slug>.svg`, and no live row carries those slugs), but six of them are
the source material for the derived `<slug>.webp` tiles that *are* published, and `collectstatic`
ships the originals regardless. Clear the originals out, or get permission in writing, before this
goes anywhere public - deriving a tile from a graphic is not a licence.

Opening those ten files rather than trusting their names found two more problems, both of which
had already been published as tiles and are now parked in `images/rejected/`: `quantum.png` is a
**FAAC Quantum sliding barrier**, not the Evolis Quantum card printer it was filed under, and
`cards.jpg` is an **IDStore.us promo graphic** with the reseller's logo across the top and an IDST
fingerprint watermark over the middle - which survived the trim, because the watermark is inside
the subject's bounding box. `evolis-quantum` and `blank-pvc-cards` are back on their drawn plates.
A third file, `static/img/products/morphomanager.jpg`, is a stock isometric "software team"
illustration with no equipment in it. The lesson is the one the repeat check above exists for:
a filename describes what someone meant, not what the picture shows.

On 2026-10-01 six of those raw files were copied again, this time onto **live slugs** as
`<slug>.jpg` (`evolis-zenius`, `evolis-badgy-2`, `evolis-accessories`, `hikvision-minmoe`,
`idemia-visionpass`, `morphomanager`), which would have published them the moment the ladder
accepted `.jpg`. They are not usable even on licence grounds: `md5sum` shows
`evolis-zenius.jpg`, `evolis-badgy-2.jpg` and the original `zenius-2.jpg` are one and the same
printer photograph, and `evolis-accessories.jpg` is a byte copy of `ribbon.jpg` - so two cards
would have shown the wrong device, and a third would have shown a ribbon pack as "accessories".
`Product.BUNDLED_EXTENSIONS` therefore stays `("webp", "svg")`: only tiles that
`tools/prepare_product_photos.py` produced under its gates (near-white surround, 340px minimum
subject, centred inside a 960x600 frame) are publishable. Do not widen the ladder to cover the
copies - rename the source, run the tile tool on it and check the result.

## Enquiry handling

`POST /contact/` stores a `ContactInquiry`, emails the team, and redirects to a
thank-you page. Three layers keep junk out without a captcha a client has to solve:

1. a visually hidden honeypot field - a filled one is acknowledged but never stored;
2. one submission per IP per minute;
3. throwaway email domains are rejected with a readable error.

Mail delivery is a hard dependency of nothing: a SMTP outage is logged, and the
inquiry still lands in the admin.

## Improvements over the previous site

- **Server-rendered content** - full copy in the HTML, not behind a JS bundle, so search engines and link previews see the page.
- **Admin CMS** - copy, products and references change without a deploy.
- **Working enquiry pipeline** - the old form posted to a page with no persisted backend or mail path.
- **Searchable catalogue** - a shop-style grid with department tiles, brand and category facets, free-text search, five real sorts, pagination, per-product specification and cross-links to the capabilities each product serves.
- **Quote list** - a session-backed basket that collects products with quantities and hands the itemised list to the enquiry form, with or without JavaScript. No prices, because none are honoured.
- **Deeper SEO** - sitemap.xml, robots.txt, canonical URLs, per-page titles and descriptions, JSON-LD for the organisation, products and case studies, and 404/500 templates that keep navigation intact.
- **Accessibility** - skip link, landmark regions, labelled controls, `aria-expanded` menus, visible focus rings, `prefers-reduced-motion` support, keyboard-operable menus.
- **Performance** - WhiteNoise with hashed, compressed static assets, cache-backed site settings, lazily loaded images, no framework runtime shipped to the browser.
- **Localisation of detail** - `Africa/Nairobi` time zone and `en-gb` for a Kenyan audience, KES context in copy, WhatsApp as a first-class contact channel.
- **Tests** - 101 tests cover publishing rules, facets, pagination, SEO fields, the enquiry pipeline, spam controls, the sort whitelist, the session list's caps and corrupt-session handling, the fragment/redirect split, the bundled plates and photo tiles against the seed rows, the solution posters against the seed rows, the region band's drawn flags against `SERVICE_REGIONS`, and the home shelf's band order and feature/card split.

## Production checklist

Set these before going live; with them in place `manage.py check --deploy` is clean:

```
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<50+ random characters>
DJANGO_ALLOWED_HOSTS=rightpoint.co.ke,www.rightpoint.co.ke
DJANGO_CSRF_TRUSTED_ORIGINS=https://rightpoint.co.ke,https://www.rightpoint.co.ke
DJANGO_SECURE_SSL_REDIRECT=True      # also enables HSTS and secure cookies
DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

Then `python manage.py collectstatic` and run `config.wsgi:application` under
gunicorn (or any WSGI server) behind TLS.

## Tests

```bash
python manage.py test
```

Run it **without** `DJANGO_DEBUG=False`: two assertions match the unhashed static URLs
(`/static/img/brands/idemia.svg`, an exact `/static/img/solutions/electric-fencing.webp`), so
manifest storage answers with hashed names and the suite reports two failures that are not
real. Keep that env var for `collectstatic` instead - `STORAGES` is decided when settings is
imported, so a default (DEBUG) run copies files but skips manifest post-processing and the next
production-mode page load dies with `Missing staticfiles manifest entry`. After any CSS change:
`DJANGO_DEBUG=False python manage.py collectstatic --noinput --clear` (the hash changes with the
content, so without `--clear` superseded copies pile up in `staticroot/`).

For the local server, `python manage.py runserver 8017` - and check the port before believing a
restart happened (`netstat -ano | grep :8017`): a previous `--noreload` child can survive and keep
serving old templates, which makes fixed bugs look unfixed. The settings module is
`config.settings`.

## Deploying

The app is a standard WSGI project, so any host that runs Python or Docker will
work. `Dockerfile`, `.dockerignore`, `Procfile` and `docker-compose.yml` are
included.

Rehearse the production image locally (needs Docker):

```bash
docker compose up --build      # http://127.0.0.1:8000, Postgres + gunicorn
```

The compose run migrates and seeds on start, and `DJANGO_SECURE_SSL_REDIRECT=False`
there because TLS terminates outside the container.

On a hosted platform, point it at the repository or image and set:

- Build: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- Release/migrate: `python manage.py migrate --noinput && python manage.py seed`
- Start: `gunicorn config.wsgi:application --bind :$PORT --workers 3 --threads 2`
  (the `Procfile` already does this; Render/Railway read it)
- Environment: everything in `.env.example`, at minimum `DJANGO_DEBUG=False`,
  a real `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`,
  `DJANGO_SECURE_SSL_REDIRECT=True` and SMTP credentials for the enquiry mail.

Verified: the WSGI application answers 200 on every route with `DEBUG=False` and
hashed static storage, `manage.py check --deploy` is clean with the SSL flags set,
and the test suite passes. Not verified: `docker build` and a live gunicorn run -
Docker is unavailable in this environment and gunicorn does not start on Windows
(it needs `fcntl`). Run `docker compose up --build` once on a Linux or Docker
capable machine before the first production deploy.

Media uploads (`/media/`, product and solution photos) live on the container's
filesystem. Attach a persistent volume, or switch `STORAGES["default"]` to
S3/DigitalOcean Spaces before relying on admin uploads in production.

### Vercel, where the database is not a database

`vercel.json` + `build_files.sh` deploy the site to Vercel, and `config/settings.py`
points SQLite at `/tmp/db.sqlite3` when `VERCEL` is set (`BASE_DIR/db.sqlite3`
everywhere else) because the project directory is read-only there. The consequence
is bigger than a path: `/tmp` is not durable storage, so the catalogue only exists
because the build recreates it. `build_files.sh` therefore runs `migrate` **and**
`seed` - drop either one and `/products/` renders its empty state, which looks
exactly like "the product images are missing" while every `.webp` and `.svg` is
serving fine from the CDN. Two things follow, and neither is fixable by editing
templates:

- Content an editor adds in `/admin/` on Vercel lasts until the next deploy, then
  is gone. Treat the deployed site as read-only until it has a real database
  (`psycopg2-binary` is already installed, so `DJANGO_DB_ENGINE`/`DJANGO_DB_NAME`
  pointing at Postgres is the smallest honest upgrade).
- Enquiry mail is the only thing that writes at request time, and on Vercel it
  cannot survive anywhere but an external inbox.

