# Shared HTML Pages

Small Firebase app for shareable HTML/JS pages whose state syncs live between visitors.
Two page kinds:

- **Custom pages** - free HTML/JS stored per page, rendered in a sandboxed iframe with a
  `shared.set` / `shared.subscribe` state bridge, per-task and per-page comments, and linkify.
- **List pages (`type: "list"`)** - a uniform hosted task-list component
  (`public/components/list.html`). Every list page shares the same component; its own content
  (title, subtitle, seed tasks, display-name map) lives in its shared state under the `_list`
  JSON key, so a fix or design change ships once for all lists. Checks, sub-items, edits,
  comments and overrides stay in the page's own state keys.

Access modes per page: public link, password, or Google sign-in restricted to listed addresses,
with separate reader/editor lists. Page creation is restricted to the owner address in config.

## Repo layout
- `app/` - shell source: `app.js` (UI, owner dashboard, component loader), `bridge.js`
  (sandboxed iframe bridge: shared state, comments, linkify), `config.example.js` (copy to
  `app/config.js` and fill in your Firebase web config + owner address), `template.js`,
  `security-gen.cjs` (RTDB rules generator - the rules file is generated, never hand-edited).
- `public/` - hosting root: `index.html`, `style.css`, `cover.png`, `components/list.html`.
  The bundle `public/app.js` is built, not committed.
- `database.rules.example.json` - rules generated with a placeholder owner; regenerate for
  your owner address.
- `admin-page.mjs` - CLI admin for pages: `create page.json | revise PAGE_ID page.html | set-type PAGE_ID list|none`.
- `firebase.json` - hosting + rules + auth config (edit the placeholders).

## Setup
```
npm install
cp app/config.example.js app/config.js   # fill in your Firebase web config and ownerEmail
firebase login
export FIREBASE_PROJECT=your-project-id
export OWNER_EMAIL=you@example.com       # full-admin Google address
node app/security-gen.cjs                # writes database.rules.json
npx esbuild app/app.js --bundle --minify --format=esm --outfile=public/app.js
firebase deploy --only database,hosting
```

## Day to day
- New page: create it in the owner dashboard (pick "uniform task list" or custom HTML),
  or `node admin-page.mjs create page.json`.
- Turn an existing custom page into a list page: write its `state._list` JSON, then
  `node admin-page.mjs set-type PAGE_ID list` (the stored html stays as a snapshot).
- Roll back a list page to its stored custom html: `node admin-page.mjs set-type PAGE_ID none`.
- Change rules only through `app/security-gen.cjs`, then `firebase deploy --only database`.

## Data model
- `/pages/<id>`: `{title, html, state, type?}` - `html` is the stored custom page (snapshot for
  list pages), `state` holds flat shared keys (`_ready` required; `_list` JSON for list pages;
  `cm_*` reserved for comments; strings <= 16000 chars).
- `/policies/<id>`: `{mode, readers, editors, publicEdit, ...}` - pipe-delimited address lists.
- `/owned/<id>`, `/meta/<id>`: owner index and public metadata.

## Limits
100k chars HTML per page, 16k per shared value, inline JS/CSS only (external libs/images blocked
by CSP), last-write-wins. Built for the Firebase Spark free tier - keep it that way.
