# Shared HTML Pages

Firebase app for shareable HTML/JS pages with live-synced state, comments and per-page access.
Install this source in **your own Firebase project**. Do not copy another installation's configuration or database.

- **Uniform lists:** `type: "list"` loads `public/components/list.html`. All list pages in one installation share that component; each page keeps its own tasks, checks, comments and edits.
- **Custom pages:** inline HTML/CSS/JS runs in a sandboxed iframe with the `shared` state bridge.
- **Access:** Google reader/editor lists, public links, or a shared password. Only the configured Google owner can create/manage pages in the app.

## Give this to your AI assistant

Copy the following request. It describes installation work, not a subscription or permission for future updates.

> Install Shared HTML Pages from https://github.com/bard1988/shared-html-pages in a new Firebase project that I own. Read the current README and source before making changes; use the existing implementation, not a rebuild from a description. Ask me to confirm the target Google/Firebase account, project ID, owner Google address and database region. Stay on Firebase Spark with no billing account, paid upgrade, Cloud Functions or other paid services. Keep project configuration and all page/task data separate from the upstream source. Follow the installation and verification steps in this README, including Google redirect-domain configuration and the central list component. Use interactive sign-in; never ask me to paste passwords, refresh tokens or service-account keys into chat or publish them. Before deploying, show the target project and settings. Do not import anybody else's pages or data. Report the deployed URL, installed source commit, files changed, tests actually passed and anything unverified. Do not claim success from a build alone. Save a local installation runbook that you will load when handling this app. Whenever I ask you to create a new page, first check the upstream source against the installed commit and tell me if newer code exists. This is a discovery check, not permission to merge, build or deploy an update that could affect existing pages. Apply updates only under my agreed authority; do not set up recurring monitoring or automatic updates.

## 1. Prerequisites and source

Use Git, npm and **Node.js 22 LTS**. The resolved Firebase CLI version's own `engines` requirement is authoritative. Commands below use a POSIX shell; on Windows use WSL or adapt environment-variable syntax.

```sh
git clone https://github.com/bard1988/shared-html-pages.git
cd shared-html-pages
npm install
npx firebase --version
git rev-parse HEAD
```

This repository currently uses version ranges and has no committed lockfile, so dependency resolution can change. Keep the generated `package-lock.json` privately with your installation for reproducibility. Do not assume `npm ci` works before a lockfile exists. Record Node, npm, Firebase CLI and the source commit.

## 2. Create your Firebase services

In the [Firebase console](https://console.firebase.google.com/), using the account you confirmed:

1. Create a **new** project on the no-payment-method **Spark** plan. Analytics is not needed. Stop if asked to attach billing or upgrade to Blaze. Check [current pricing and quotas](https://firebase.google.com/pricing); free quotas are finite and service can stop when they are exceeded.
2. Register a **Web app** under Project settings. Copy its Firebase web config locally. These are public browser identifiers, not server credentials.
3. Create **Realtime Database** (not Firestore). Choose the region deliberately; copy its exact database URL rather than constructing one. Start in **locked mode**, never open test rules.
4. In Authentication, enable **Google** and choose the project's support email. Enable **Email/Password** only if shared-password pages are wanted. Anonymous auth is not needed.
5. Confirm the Hosting domain is an authorized domain in Authentication. For the default hosting site this is normally `PROJECT_ID.web.app`; use the actual site/domain reported by Firebase if different.
6. This app uses `signInWithRedirect`. Set `authDomain` to the same Firebase Hosting domain from which users will open the app. In the Google OAuth web client used by Firebase Auth, authorize `https://YOUR_HOSTING_DOMAIN/__/auth/handler` as a redirect URI. Keep the existing Firebase handler too. See [Google sign-in](https://firebase.google.com/docs/auth/web/google-signin) and [redirect-domain requirements](https://firebase.google.com/docs/auth/web/redirect-best-practices). Do not invent a client secret or put one in browser code.

The repo's `firebase.json` has an `auth.providers` example, but **the deploy command below deploys only database rules and Hosting, not provider setup**. Verify providers and domains in the console explicitly.

## 3. Local configuration and owner rules

```sh
cp app/config.example.js app/config.js
export FIREBASE_PROJECT='your-project-id'
export OWNER_EMAIL='owner@example.com'
```

Replace all example values with **your** settings:

- `app/config.js`: exact web config, exact `databaseURL`, same-origin `authDomain`, and `ownerEmail` equal to the verified Google owner's address.
- `OWNER_EMAIL`: the **same exact owner address** used in `app/config.js`. Confirm its spelling/case against the signed-in account. The generated owner rule uses exact equality.
- `firebase.json`: replace the example support email and both example redirect URIs in the `auth` section. Preserve the existing Hosting headers/CSP, hosting root and rules path.

`app/config.js`, `database.rules.json`, `.firebaserc`, `public/app.js` and `backups/` are ignored by Git. `firebase.json` is **tracked**, so keep its installation-specific changes private and review conflicts during updates. The owner address ships in the browser bundle as part of the app's design; it is not a secret. Never publish real installation settings to this upstream repository.

```sh
node app/security-gen.cjs
npx esbuild app/app.js --bundle --minify --format=esm --outfile=public/app.js
```

The generator writes `database.rules.json`. Do not deploy `database.rules.example.json` or hand-edit the generated rules. Check that no example project/owner remains in the configured files, the owner matches in config and rules, and `public/components/list.html` exists. Preserve the `_ready` state marker.

## 4. Authenticate, verify the target, deploy

```sh
npx firebase login
# On a remote machine without a localhost callback, use:
# npx firebase login --no-localhost
npx firebase login:list
npx firebase projects:list
```

Confirm the selected account has rights to the intended new project. If several accounts are signed in, select the correct one with `npx firebase login:use YOUR_EMAIL` and verify again. Authentication is interactive; do not use pasted tokens or export credentials into this repository.

After the owner confirms the target:

```sh
npx firebase deploy --project "$FIREBASE_PROJECT" --only database,hosting
```

`FIREBASE_PROJECT` alone does **not** select a Firebase CLI target; the explicit `--project` flag does. There is no need to run `firebase init` over these source files, which could replace the supplied rules or Hosting config. If prompted to create the default Hosting site, verify its project and proceed only within the confirmed setup.

Open the **exact Hosting URL returned by the deploy**, on the same domain chosen for `authDomain`.

## 5. Verification before calling it installed

Use disposable test content and at least an owner session plus separate test sessions/accounts. Get consent before adding real people or using their accounts. A local build does not verify live permissions.

- Owner Google sign-in returns to the dashboard and can create a uniform list and a custom page. A different Google account cannot create/administer pages.
- In a list, add/edit a task, add a nested task, check it, comment and refresh. Changes persist and appear in a second authorized session. Confirm `/components/list.html` loads; do not generate a separate copy for each list.
- For Google-restricted pages: a listed reader can view but **cannot save**, a listed editor can save, and an unlisted or signed-out session cannot read page content/state. Test save failure, not just whether buttons are visible.
- Public view-only pages can be read without sign-in but reject saves; public-edit is a separate, explicit audience choice. Never use real private test content in a public page.
- If Email/Password was enabled, test the correct password, a wrong password and owner password rotation on the **same page link**. Previous password identities must lose access.
- Check a custom page's state bridge, an external link, comments and the console for CSP/network errors. External scripts, images and fetches inside custom content are intentionally blocked.
- Check on a phone-sized screen and after reload. Offline saves must not be reported as confirmed.

Report each pass/failure and each test not run. Keep credentials and disposable content out of public reports. This is a small app, not a substitute for an independent security audit.

## Architecture and list data

- `app/app.js`: owner dashboard, auth, page access flow, component registry/loader.
- `app/bridge.js`: sandbox/state/comment/link bridge.
- `public/components/list.html`: shared list UI and behavior, deployed once per installation.
- `/pages/PAGE_ID`: `{title, html, state, type?}`. For list pages, `type` is `list` and stored `html` is not rendered. Removing `type` returns to stored HTML, which may be empty for a newly created list.
- `/policies/PAGE_ID`: access policy; `/owned/PAGE_ID`: owner index; `/meta/PAGE_ID`: public gate metadata. Policy changes are owner-only in the client rules.

A fresh list created in the dashboard is empty and can be filled through its UI. Optional seed/config is a **JSON string** at `/pages/PAGE_ID/state/_list`, not an object:

```json
{
  "title": "Example checklist",
  "subtitle": "Generic sample content",
  "tasks": [
    {"id": "t1", "text": "First task", "order": 1, "subs": ["First subtask"]}
  ],
  "names": {},
  "statusNames": ""
}
```

Serialize with `JSON.stringify`. Keep seed IDs stable and unique, using safe letters/digits/underscores/hyphens. IDs also identify checks, edits and comment threads; replacing them loses their associations. `_list` and other shared string values are limited to 16,000 characters. HTML is limited to 100,000 characters and title to 100. State values are strings, finite numbers or booleans, with last-write-wins on the same key. Comments use reserved `cm_` keys. Preserve existing state; never replace the whole database to update a page or a component.

## Optional page-admin CLI

Prefer the dashboard for first setup. `admin-page.mjs` uses the Firebase CLI's authenticated administrative session, which has broader power than page readers/editors. It is not a credential to give collaborators.

```sh
export FIREBASE_PROJECT='your-project-id'
# The script invokes `firebase`, so use the installed local executable:
export FIREBASE_CLI="$PWD/node_modules/.bin/firebase"
node admin-page.mjs create page.json
node admin-page.mjs revise PAGE_ID page.html
node admin-page.mjs set-type PAGE_ID list
node admin-page.mjs set-type PAGE_ID none
```

Minimal `page.json` for an empty, owner-only list:

```json
{"title":"Example list","type":"list","mode":"google","readers":[],"editors":[]}
```

`create` accepts public or Google mode, not password mode; use the dashboard for passwords. It does **not** import a supplied `state` or `_list` field: seed data must be written separately to the exact new page state path using an authorized narrow update. Creation uses four writes and can partially fail; inspect the exact page before retrying. Use the actual Hosting URL if it differs from the default URL the script prints. `revise` requires existing nonempty stored HTML; it does not affect a list's central component. Before converting an existing page to `list`, back up that page privately, write compatible `_list` config while preserving all state, then change only its `type`. Removing `type` is useful only if a valid custom-HTML snapshot exists.

## Updates: check first, deploy separately

There is **no built-in updater, notification service or AI subscription**. A guide cannot push messages into another person's AI assistant. GitHub Watch notifications are for whoever subscribes; they are not automatic deployment or AI access.

For each independent installation, keep the upstream URL and installed commit. The installing AI should save this rule in its local installation runbook: **before creating each new page, check upstream freshness against the installed commit**. Load that runbook when handling the app. Report newer code and material changes; do not silently merge or deploy. A static document cannot enforce this behavior in an AI that does not load or follow it. This event-driven check needs no recurring watcher. If upstream cannot be reached, report freshness as unverified rather than claiming the installation is current. A failed discovery check is not evidence that a code update is required.

For that pre-create check, or when the owner explicitly asks, fetch without merging first:

```sh
git status --short
git rev-parse HEAD
# If origin is the source repository above:
git fetch origin
git log --oneline HEAD..origin/main
git diff HEAD..origin/main -- app public admin-page.mjs firebase.json package.json
```

A fork may use a separate `upstream` remote; confirm the remote before running these commands. Review changes and any migration requirements. **Do not blindly pull, reset or overwrite local configuration.** Save local changes, keep private backups of configuration and affected data, choose the exact reviewed commit, reconcile `firebase.json`, reinstall dependencies if needed, regenerate rules only if required, rebuild, preview/test, then get deployment approval within that owner's agreed scope. Deploy to that installation's explicit project only. Update the installed-commit record after success.

A component update affects all list pages in that installation, but does not require overwriting their state. Source rollback means rebuilding the prior verified commit with that installation's config; data migrations need their own backup/rollback plan. Stable tags, release notes and an opt-in update checker could be added later, but are **not implemented or subscribed here**.

## Troubleshooting and limits

- `firebase: command not found`: use `npx firebase`; for `admin-page.mjs`, set `FIREBASE_CLI` as above.
- Owner dashboard missing / permission denied: confirm the exact Google account, verified email, config owner, generated owner rule, deployed rules and project/database URL. Do not open all rules as a workaround.
- `auth/unauthorized-domain` or redirect loops: check authorized Hosting domain, same-origin `authDomain`, Google provider and OAuth redirect URI. Rebuild after changing config.
- Database errors: confirm **Realtime Database** exists, URL/region is exact, the owner rules were generated/deployed to the right project, and `_ready: true` is present.
- List component missing/stale: verify `public/components/list.html` is included in the Hosting deploy and reload. Changing only stored per-page HTML does not change a `type: list` page.
- Shared-password mode uses one Firebase Auth identity per page, not a separate identity per person. Password holders can change that identity through Firebase APIs and lock others out; the owner can rotate to a new identity. Prefer Google for personal permissions or sensitive data.
- Author/comment ownership checks in the UI/bridge are not a full per-comment database authorization boundary; editors can write shared state directly. Do not promise tamper-proof attribution or history.
- No CRDT, built-in version history, automatic backups or automatic updates. Service quotas are finite; do not attach billing to bypass a free-tier limit without new approval.

## Verification of this guide

Reviewed against the published source on 2026-10-30. A fresh checkout was dependency-installed on Node 22, the rules generator ran with a placeholder owner, and the shell bundle built successfully. Firebase CLI command syntax was checked locally. **A new live Firebase project was not created or deployed for this guide, and the full live permission matrix was not re-run.** Each installer must complete it for their own project.

Official references: [CLI](https://firebase.google.com/docs/cli), [Realtime Database setup](https://firebase.google.com/docs/database/web/start), [Google sign-in](https://firebase.google.com/docs/auth/web/google-signin), [redirects](https://firebase.google.com/docs/auth/web/redirect-best-practices), [pricing](https://firebase.google.com/pricing).
