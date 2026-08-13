# Haohaotiantian → 水浒传 redesign: project plan

> Working document. Phases 0–5 are specified well enough to execute; the hero
> mechanics in Phase 7 are still under design — see
> [Hero mechanics — open design questions](#hero-mechanics--open-design-questions).
>
> Two sections carry decisions that must be settled *inside* Phase 0, because
> later phases inherit the schema it writes:
> [User-created vocab lists](#user-created-vocab-lists-decisions) and the
> day-boundary question in [Phase 6](#phase-6--progression-primitives).

## Context

Haohaotiantian is a working daily-Chinese-vocab product: this serverless backend (Python 3.13 + AWS SAM) emails one HSK word per day and serves quiz/review APIs, plus a separate Vue frontend ([vocab-frontend-vue](https://github.com/em-shea/vocab-frontend-vue)).

The redesign wraps this in a Water Margin frame — you climb Mount Liang and gather the 108 heroes by keeping up daily practice. That is three distinct pieces of work stacked on top of each other:

1. **A new visual language** (aged paper, woodblock, zero radius) replacing Bootstrap 4.
2. **A bilingual UI** — every string keyed with `en`/`cn`, toggled by an immersion switch. This does not exist at all today.
3. **A progression + collection layer** — streak, provisions, stone tablet, 108 progressively-revealed hero cards. Neither the streak nor the collection has any backend today.

The intended outcome: ship the redesigned, bilingual site first as a standalone improvement, then layer progression and collection onto it — each phase independently shippable.

### Constraints that shape everything below

**The frontend toolchain is dead.** Vue 2.6, Vue CLI 3, eslint 5, Amplify v3, axios 0.19 loaded from a CDN, Bootstrap 4 from a CDN, ~22 open dependabot branches. The redesign rewrites every template anyway, so the decision is a **Vue 3 + Vite rewrite** in the existing repo — reusing its S3/CloudFront deploy workflow rather than doing the same template work twice on an EOL stack.

> **Frontend deploys were broken and are now fixed (2026-08-13).** `master` could not be built at all: its 2023 lockfile pinned `node-sass ^6.0.1`, which needs native compilation and does not support Node 18, so `npm install` failed. The CircleCI → GitHub Actions migration had been made on `staging` and never merged, so pushing to `master` triggered nothing — prod's `index.html` in S3 was dated 2023-11-14. `staging` was merged into `master` (keeping master's `.env.production`, which alone had the correct prod Cognito pool), and the deploy workflow now fails the build if the bundle carries the wrong pool or API URL for its branch. Phase 4's cutover depends on this pipeline working.

**The design mockup is not yet in hand.** `Haohaotiantian Redesign.dc.html` was not available when this plan was written. The upstream brief is `design-handoff-shuihuzhuan.md` and a 25-shot current-state screenshot set exists for regression comparison. This plan is built from the written redesign notes, which carry the full palette, type stack, and section flow. **Before Phase 2 starts, drop the `.dc.html` into `vocab-frontend-vue/design/` so token values and section markup can be matched exactly.**

**The collection layer ships to a beta cohort, not to everyone.** Progression is a year-long time-based mechanic against a live subscriber base. It deploys to prod dark behind a per-user flag rather than to a third AWS environment — see [Rollout and isolation strategy](#rollout-and-isolation-strategy-applies-to-phases-68). This keeps the redesign (Phases 0–5) on a normal cutover, unblocked by the risky part.

---

## Phase 0 — Backend hygiene (blocking, ~medium) — IMPLEMENTED

Fix live problems and unblock prerequisites before adding surface area. This phase grew when the list and progression work was traced through the code — it is no longer a quick pass, and it is the phase where the schemas every later phase depends on get written.

> **Status:** SHIPPED to staging and prod on 2026-08-11. 120 tests green, coverage 86% (floor 70%). List metadata seeded in both environments (`scripts/seed_vocab_lists.py`); prod verified with `GET /sample_vocab` and `GET /review` serving six data-driven lists, and `GET /quizzes` / `GET /sentences` live for the first time.
>
> **Regression shipped and fixed the same day:** making `VerifyAuthChallengeResponse` decode the sign-in code introduced a read of `os.environ['OTP_SECRET_KEY']`, but that function's template resource had **no `Environment` block at all** — only `CreateAuthChallenge` had ever needed the key, to sign. Every staging sign-in failed with `UserLambdaValidationException: ... 'OTP_SECRET_KEY'`. Unit tests could not catch it: `conftest.py` sets env vars for the whole test process, so the handler passes regardless of what the template provisions. Added `src/tests/unit/test_template_env_vars.py`, which asserts every `os.environ['X']` a function requires — resolved transitively through the layer modules it imports — is declared for that function. Note the failure only reproduces on a *correct* code: the env read sits after the constant-time compare, so a wrong code returns before reaching it.
>
> **Prod baseline before the change:** 624 users, 468 active subscriptions, 343 emails in the 2026-08-11 send. The user GSI partition holds 1541 items ≈ 500KB, i.e. **half** the 1MB page cap — so the unpaginated query was not yet dropping anyone, and the pagination fix is headroom rather than a behavioural change. Compare tomorrow's send against 343.
>
> **Blocker found and cleared:** every function declared `Runtime: python3.11`, which AWS deprecated on 2026-06-30, with **function updates disabled after 2026-08-31** — nothing in this plan could have deployed after that date. Upgraded to python3.13; see [Runtime upgrade](#runtime-upgrade-blocking-all-deploys).
>
> **Two live bugs were found beyond the ones listed below**, both the same class as the `get_sentences` prefix bug and both in code the progression layer depends on: `quiz_results_service.query_dynamodb` queried `SK begins_with('QUIZ#')` against keys written as `DATE#<date>#QUIZ#<id>`, and its date filter compared a `%Y-%m-%d` string against an isoformat one, excluding the boundary day. `format_quiz_results` also sliced the quiz id out of the key with `SK[5:]`, returning `<date>#QUIZ#<id>` — visible in `get_user_activity` output today. All three are fixed; `GetQuizResults` would have returned nothing if deployed as it stood.

**Live bugs found during exploration:**

- `src/send_daily_email/app.py:129` opens `announcements_template.html`, but the packaged file is `src/send_daily_email/announcements.html`. `get_announcement()` only wraps the S3 `get_object` in try/except — the file open is unguarded. On any day an announcement file exists, the handler raises before sending **any** email, and the function has `MaximumRetryAttempts: 0`. Fix the filename and extend the try/except to cover the read.
- `src/get_user_activity/app.py` (~line 40) assigns `user_activity[date]['review_words']['sentence'] = …` where `review_words` is a list — `TypeError` whenever a sentence matches a review word. Index the correct element.
- `src/get_sentences/app.py` queries `SK begins_with('SENTENCE')`, but `set_sentence` writes `DATE#<date>#SENTENCE#<id>`. The read path can never match. Fix the prefix.
- `src/user_pool_triggers/create_auth_challenge/app.py` signs the OTP as `jwt.encode({'u': username}, …)` with no `exp` claim and a constant payload — a given user's login code never changes and never expires. Add `exp` (10 min) and a nonce.
- `src/send_daily_email/app.py:175` does `todays_words[subscription.list_id][0]['word']` on a plain dict (`get_daily_words()` casts the `defaultdict` away at line 139). Any subscribed list with no `DATESENT#<today>` item raises `KeyError` — and `assemble_html_content` is called at line 74, **outside** the per-user `try/except` that begins at line 75. One user subscribed to one wordless list kills the entire day's send, with `MaximumRetryAttempts: 0`. This is already reachable today (`set_todays_words` sets `todays_words[list_id] = None` on a per-list failure at `app.py:46`), and user-created lists make it routine. Move the `assemble_html_content` call inside the `try`, and skip a subscription whose list has no word rather than indexing blindly.
- `src/set_subscriptions/app.py:28` reads `event_body['cognito_id']` from a **`POST /set_subs` with no authorizer** (`template.yaml:167-171`). The identity is caller-supplied and unverified, so anyone who knows a user's Cognito sub can add or remove that user's subscriptions. Tolerable while every list is public HSK content; not tolerable once lists are user-owned. Decide here whether `/set_subs` keeps public sign-up (needed — the home page subscribe band is anonymous) with a separate authed path for changes to an existing user's subscriptions.

**Prerequisites for later phases:**

- **Make vocab lists data-driven.** Already on the README roadmap. Move the six hardcoded lists out of `src/layer/python/vocab_list_service.py` into DynamoDB `LIST#<id>` / `METADATA` items, keeping the existing UUIDs so nothing breaks. Required for the 5a home page's "bring your own vocab list" and for the 成语 list. This is not a lift-and-shift — see [User-created vocab lists](#user-created-vocab-lists-decisions) for the schema and fan-out consequences that have to be settled *with* this move, not after it.
- **Stop caching the list set at import time.** `src/layer/python/review_word_service.py:15` and `src/get_review_words/app.py:14` both run `all_lists = vocab_list_service.get_vocab_lists()` at **module level**. Once that call reads DynamoDB, the result is frozen for the life of the warm Lambda container — a newly created list stays invisible until recycle. Move both inside the handler before the data source changes.
- **Paginate `query_all_users`.** `src/layer/python/user_service.py:64-72` is a single `table.query` on `GSI1PK = 'USER'` with no `LastEvaluatedKey` loop: one partition, hard 1MB cap, silent truncation past it. Phase 6's "free fan-out" argument rests entirely on this loop covering every user — past the cap, those users get no email **and** no reconcile, with nothing in the logs. Add the pagination loop now.
- **Make attribute reads defensive.** `_format_user_data` (`user_service.py:106-112`) indexes user metadata directly — `item['Character set preference']`, `item['User alias']`, and so on. Every new attribute this plan adds (`Language preference` in Phase 2, `Feature flags` in the rollout section) would `KeyError` on every user record written before it existed. Switch to `.get(…, default)`. Same for `review_word_service.format_word_body` (`:64-77`), which hard-indexes `Traditional`, `Audio file key`, `HSK Level` and `Difficulty level` on every word — user-uploaded words will not always carry all four.
- **Deploy the commented-out read endpoints.** `GetQuizResults` (`template.yaml:315-341`) and `GetSentences` (`template.yaml:371-397`) are written but not deployed. The progression layer needs quiz history readable. Uncomment after fixing the bugs above.
- **Make the user queries and dispatch explicit.** `user_service.query_single_user` uses `Key('SK').gt('LIST')` and `query_single_user_with_activity` uses `SK > 'DATE#<date>'` — open-ended ranges. In ASCII, `DATE# < HERO# < LIST# < PROGRESS < USER#`, so the Phase 6/7 item types land inside both ranges. They would fall to the `else` branch at `user_service.py:154` and print rather than crash, so this is not fatal — but `_format_user_data` dispatches on **substring** matches (`if 'USER' in item['SK']`), which is fragile against any new key containing those tokens. Bound the queries and switch the dispatch to prefix matching **before** new item types exist, not after.

**Files:** `src/send_daily_email/app.py`, `src/get_user_activity/app.py`, `src/get_sentences/app.py`, `src/user_pool_triggers/create_auth_challenge/app.py`, `src/layer/python/vocab_list_service.py`, `src/layer/python/list_word_service.py`, `src/layer/python/review_word_service.py`, `src/layer/python/user_service.py`, `src/get_review_words/app.py`, `src/set_todays_words/app.py`, `src/sample_vocab/app.py`, `template.yaml`.

**Done when:** `pytest` green (coverage floor 70% per `pyproject.toml`), staging deploy healthy, an announcement-day email actually sends.

---

## Decisions taken (2026-08-13)

| Decision | Status | Notes |
|---|---|---|
| **Practice sentences UI** | **Off** | Backend is live in prod; the UI ships but is gated by `SENTENCES_ENABLED` in `vocab-frontend-vue/src/featureFlags.js`. Profile shows the previous placeholder card and `/sentences` redirects to `/profile`. Flip one boolean to enable. |
| **Email verification** | **Stays auto-confirm** | `pre_sign_up` continues to auto-confirm, so no verification email is sent and anyone can subscribe another person's address. Accepted for now; revisit in Phase 3 with the subscribe-flow redesign. |
| **Subscription endpoints** | **Split, shipped** | `POST /set_subs` is public sign-up only and rejects existing users; `POST /subscriptions` is Cognito-authorized and takes identity from token claims. Both enforce list visibility. |

Because email verification stays as-is, the argument in [User-created vocab lists](#user-created-vocab-lists-decisions) holds: the split is the right shape, since there is no email round-trip to piggyback on. If double opt-in is adopted later, revisit whether `/set_subs` needs to stay public at all.

---

## Operational state (2026-08-12)

**Function sizing**, set from observed prod usage rather than defaults:

| Function | Was | Observed | Now |
|---|---|---|---|
| `SendDailyEmail` | 128MB / 120s | 101MB, 57s for 343 emails | 512MB / 300s |
| `SetTodaysWords` | 128MB / 120s | 102MB, 6.9s for 6 lists | 512MB / 300s |
| `BackupDynamoDBToS3` | 128MB / 120s | **118MB (92%)**, 31s | 1024MB / 300s |

Memory on `SendDailyEmail` grows with subscriber count (every user is held in memory at once) and on `BackupDynamoDBToS3` with total table size (it scans and `json.dumps` the whole table). `SetTodaysWords` grows with the number of lists needing a daily word — which is exactly what user-created lists add.

**Alarms.** The pre-existing alarms only match the string `Error` in the logs, which misses the failures that actually lose a day's email: a timeout, an OOM kill, or the schedule not firing. Added service-metric alarms on both scheduled functions — did-not-run (`Invocations < 1` over 24h, `TreatMissingData: breaching`, since missing data *is* the failure), errored (`Errors >= 1`), and a duration warning at 240s of the 300s limit.

> **The alarm topic had zero subscribers in both prod and staging.** The template declares an email subscription, but SNS email subscriptions require clicking a confirmation link and AWS deletes unconfirmed ones after ~3 days, so it lapsed silently long ago — no alarm in this stack, old or new, could notify anyone. Re-subscribed 2026-08-12 and **confirmed 2026-08-13**; both topics now show a confirmed email subscription. Nothing in the template detects a future lapse, so it is worth re-checking with `aws sns list-subscriptions-by-topic` occasionally.

**First run of the new daily pipeline (2026-08-12, 20:00 UTC):** 344 emails against a 343 baseline, 47.1s (down from 56.4s), 114MB of the new 512MB limit. No errors. Confirms the data-driven list path and `get_subscribed_list_ids()` work against 468 real subscriptions.

---

## Runtime upgrade (blocking all deploys) — DONE

`sam validate --lint` reported `E2531` against every function in `template.yaml`:

> Runtime 'python3.11' was deprecated on '2026-06-30'. Creation was disabled on '2026-07-31' and update on '2026-08-31'.

This was not a lint nit — after **2026-08-31** AWS refuses to update the function code, so `sam deploy` fails and the entire plan is stuck behind it. Unrelated to the redesign, predating it, and the hardest deadline in the project.

**Upgraded to `python3.13`** across all 20 functions, the layer's `CompatibleRuntimes`, and the CI workflow's `python-version`. Deployed to staging and prod on 2026-08-11 — confirmed all 20 functions in each stack now report `python3.13`, well ahead of the 2026-08-31 cutoff.

Why 3.13 rather than the 3.14 the linter suggests: per cfn-lint's runtime lifecycle data both deprecate on **2029-06-30**, so the newer version buys no extra runway, while 3.13 has broader wheel availability for the dev dependencies CI installs (`moto`, `pytest-cov`). If that changes, moving 3.13 → 3.14 is the same one-line-per-function edit.

Verified: `sam validate --lint` no longer reports `E2531` (the remaining `E3638`/`E3045`/`W30xx` findings all pre-date this work and concern `ProvisionedThroughput` alongside `PAY_PER_REQUEST` and S3 `AccessControl`); `sam build` succeeds for all 20 functions with `PyJWT==2.10.1` resolving; and the full suite is green on a real 3.13 interpreter.

> **The local `.venv` is still Python 3.9**, which is both EOL as a Lambda runtime and now two majors behind what deploys. Tests pass on it, but it is not what runs in production — rebuild it on 3.13 so the two match.

---

## User-created vocab lists (decisions)

*The `LIST#<id>` / `METADATA` schema written in Phase 0 is the one user lists inherit, so these decisions belong there even though the upload UI ships in Phase 3. Getting them wrong means a migration later.*

### Why this is more than a data move

Six hardcoded admin lists and an unbounded set of user lists are not the same shape. Four hot paths currently loop over **every list in existence**, one DynamoDB query each:

| Path | Code | Consequence once lists are user-created |
|---|---|---|
| Daily word selection | `set_todays_words/app.py:39-47` | One full-list query + one write per list, per day, in a 128MB/120s Lambda (`template.yaml:52-53`) |
| Daily email word lookup | `review_word_service.py:28-34`, via `send_daily_email.get_daily_words()` | Same fan-out, at the head of the highest-blast-radius job in the system |
| Home page samples | `sample_vocab/app.py` | The **public, unauthenticated** home page would sample words out of strangers' private lists |
| Review/quiz reads | `get_review_words/app.py` | `GET /review?list_id=<uuid>` has **no authorizer** (`template.yaml:143-148`) and returns any list's words to anyone |

Neither `list_word_service.get_words_in_list` (`:51`, single `table.query`, no `LastEvaluatedKey` loop) nor `sample_vocab` bounds its result set.

### Decisions

**1. Ownership and visibility.** `LIST#<id>` / `METADATA` carries `Created by` (`admin` or `USER#<sub>`) and `Visibility` (`public` | `private`). The six HSK lists and the 成语 list seed as `admin` / `public`. **User lists are private by default**, and v1 ships no sharing — public user lists are a later decision, and the schema already holds the field for it.

**2. Reads follow visibility.** `GET /review` stays public but serves `Visibility: public` lists only. Owner access to a private list comes from a **second authed API event on the same `GetReviewWords` function** (`Auth: Authorizer: CognitoAuthorizer`, e.g. `/my_review`), resolving the owner from the Cognito claims and 403-ing anyone else. Same handler, same service code, one extra event in `template.yaml`. `sample_vocab` filters to `public` — it is the anonymous home page and must never see a user list.

> **Consequence to accept deliberately:** the daily email's quiz and review deep links (`send_daily_email/app.py:204-205`) are unauthenticated URLs. For a private list they must point at the authed path, so **a private-list email link requires sign-in to open**. That is a real UX change from today's one-click flow, and it is the price of private lists. Decide it now, not when the email template is rewritten in Phase 5.

**3. Subscribing.** `POST /set_subs` rejects a subscription to a private list the caller does not own — which requires the identity fix in the live-bugs section above, since the endpoint currently trusts a caller-supplied `cognito_id`.

**4. Daily words are generated only for lists with at least one active subscriber.** This is what keeps the fan-out bounded by real demand rather than by upload count, and it costs nothing to compute: `set_todays_words` derives the subscribed-list set from the GSI1 `USER` query `user_service.query_all_users()` already makes (subscription items carry `GSI1SK = USER#<sub>#LIST#<id>#<CHARSET>`, `set_subscriptions/app.py:121`). Admin lists are always included so the public home page and sample endpoint stay populated.

**5. Upload format — a superset of `hsk_vocab.csv`.** That file's columns are `Word,Pronunciation,Definition,HSK Level`; it carries **no traditional characters**, while `format_word_body` hard-indexes `Traditional` and traditional-set subscribers render it directly (`send_daily_email/app.py:184`).

| Column | Required | Behaviour |
|---|---|---|
| `Word` | yes | Stored as `Simplified` |
| `Definition` | yes | Stored as-is |
| `Pronunciation` | no | Stored as `Pinyin`; derived when absent |
| `Traditional` | no | Stored as-is; derived when absent |
| `HSK Level` | ignored | User lists store `""` |

**6. Derive the missing fields at upload time, in the upload Lambda only.** `Traditional` via OpenCC `s2t` when the column is absent — phrase-aware conversion, so word-level ambiguities (发 → 髮/發, 里 → 裡/裏) resolve correctly where a character table would not. `Pinyin` via `pypinyin` (tone marks, phrase dictionary) when `Pronunciation` is absent. Store `Traditional source: user | converted` so a bad conversion can be re-run without asking for a re-upload.

> **Why write-time matters:** conversion happens once, so `opencc` and `pypinyin` (both carry dictionary data) belong in `src/create_list/requirements.txt` — **not** in the shared layer that all fifteen functions load. Every read path just reads the stored attribute.

**7. No audio for user lists in v1.** Words store `Audio file key: ""`, which is already the pipeline's "needs audio" sentinel (`get_chars_for_list_id/app.py:36`), so enabling audio later is running the existing `GenerateAudioStateMachine` against the list id — no schema change, no migration. Until then the empty key must render cleanly: `reviewWordCard.vue:12` and `Home.vue:106` already guard it with `v-if`, but **`practiceSentenceCard.vue:8` and `UserProfile.vue:100` do not** and would render a dead play button. Guard both during the Phase 4 port.

**8. Caps: 500 words per list, 10 lists per user.** Not arbitrary — 500 words keeps a list inside a single DynamoDB query page, which matters because `get_words_in_list` never paginates and `set_todays_words` picks its random word from whatever one page returns. The caps also bound the daily fan-out and the eventual Polly cost. Enforce at upload with a clear error, not silent truncation.

**Word item shape for a user list** (`LIST#<id>` / `WORD#<id>`): `Simplified`, `Traditional`, `Pinyin`, `Definition`, `Audio file key: ""`, `HSK Level: ""`, `Difficulty level` from the list-level difficulty the user picks at upload (same `Beginner`/`Intermediate`/`Advanced` vocabulary the existing lists use, so nothing downstream has to learn a new value).

**Still open:** whether user lists can ever be made public or shared, and what moderation that would require. The `Visibility` field exists so this stays a logic change.

---

## Phase 1 — Vue 3 + Vite scaffold and design system — IMPLEMENTED

> **Status:** shipped to both branches 2026-08-13, in `vocab-frontend-vue/v2/`. The Vue 2 app is untouched and still builds and deploys; nothing about the live site changed.
>
> **Bundle:** 245 KB of JS against the Vue 2 app's 1 792 KB. Fonts total 1.2 MB on disk but load selectively — Latin faces keep Google's `unicode-range` split, and only the weights a page uses are fetched.
>
> **Font subsetting is a maintained artefact, not a one-off.** `v2/scripts/build-fonts.mjs` regenerates the Ma Shan Zheng display subset (78 characters). It must be re-run when brush copy gains a character, otherwise that character silently falls back to the serif — which happened during this phase with 印 in `PrintFrame` and was only caught by looking at the rendered page.
>
> **Vite needed `define: { global: 'globalThis' }`.** `amazon-cognito-identity-js` pulls in `buffer`, which expects Node's `global`. Webpack shimmed it automatically; without it the app renders a blank page with `ReferenceError: global is not defined`. Worth knowing before porting any other Node-flavoured dependency.
>
> **Verification harness:** `v2/scripts/shoot.mjs` (Playwright) screenshots at 390 and 1120 and fails on horizontal overflow. Phase 4 needs exactly this to diff ported screens against the current-state screenshot set, so it is a script rather than ad hoc browser steps.
>
> **Still open for Phase 2:** the design mockup. `Haohaotiantian Redesign.dc.html` has not been dropped into `vocab-frontend-vue/v2/design/`, so token values are from the written brief and have not been matched against the real design.

Stand up the new app alongside the old one so the old site keeps serving until cutover.

- New `vocab-frontend-vue` app: Vue 3 + Vite + vue-router 4 + Pinia. TypeScript is optional — recommend plain JS to keep the port mechanical.
- Replace both CDN globals: `axios` as a real dependency, `vue-select` dropped or replaced (`listDropdown.vue` is trivial to rewrite against the new design).
- **Single API client module** (`src/api/client.js`) — today there are 16 inline `axios` calls across views with no wrapper. One client with the base URL and the Cognito `Authorization` header (raw JWT, no `Bearer` — the backend authorizer expects it that way).
- **Auth cleanup.** Today `main.js` configures Amplify but every actual call uses `amazon-cognito-identity-js` directly via `src/shared.js`. Pick one — recommend dropping Amplify entirely and keeping the lighter direct SDK path, porting `getSignedInUser()` / `getUserData()` / `signOut()` into a Pinia store.
- **Design tokens** as CSS custom properties: ground `#EDE4D0`, panel `#F6EFDC`, ink `#2A2318`, body `#5C5342`, muted `#8A7F68`, rule `#C9BB9C`, seal `#B03A2B`, button blue `#8DB6C6`, pinyin `#2C4A6B`, gold `#E0A93B` (dark band only). Global `border-radius: 0`.
- **Self-host the fonts** — Archivo 800/900, Instrument Sans, Noto Serif SC, Ma Shan Zheng, DM Mono, Outfit. Noto Serif SC is very large; subset it against `hsk_vocab.csv` (all six levels) plus the hero name set, or it will dominate page weight.
- **Primitive components:** `SectionHead` (brush mark + uppercase label + hairline rule — every section opens with this), `Panel`, `Button` (2px ink border, 3px hard shadow, no radius), `PrintFrame` (4px ink frame + halftone dot overlay), `ScrollRods` (page top/bottom), paper fibre texture.

**Done when:** a tokens/primitives page renders correctly at 390 and 1120, and the two existing `.env` files still drive staging vs prod.

> Note: `.env` and `.env.production` are committed and contain the Cognito pool id and web client id. Those are public client identifiers, so this is not a leak — but move them to CI secrets during the rewrite for hygiene.

---

## Phase 2 — Bilingual i18n

Do this **before** porting screens, so every ported string is keyed on first write rather than retrofitted.

- `vue-i18n` v9, with `en` and `cn` message objects mirroring the `t.*` keys in the design doc.
- **Keep this strictly separate from the simplified/traditional switch.** They are different axes: i18n is *UI chrome language*; character set is *study content rendering*. Today the character set lives in the hand-rolled store in `main.js` and is read via `$root.$data.store.state.characterSet` in `Home.vue`, `Review.vue`, `reviewWordCard.vue`, `practiceSentenceCard.vue`, `faqContent.vue`. Move it to a Pinia `preferences` store alongside the new `language`.
- **Persist both.** Character set currently resets on reload — a real bug. Persist to `localStorage`, and for signed-in users sync to the user record via the existing `POST /update_user` (`src/set_user_data/app.py`) by adding a `Language preference` attribute next to `Character set preference`.
- `Review.vue` already syncs character set into the URL as `?char=`; keep that and add `?lang=`.

**Backend touch:** `src/set_user_data/app.py`, `src/layer/python/models.py` (`User` dataclass gains `language_preference`), `src/layer/python/user_service.py` `_format_user_data` — read it with `.get('Language preference', 'en')`, since no existing user record has the attribute (see the defensive-reads item in Phase 0).

---

## Phase 3 — Home page (5a) and subscribe flow

Build the seven sections in order, prints and text alternating sides:

1. **Quest** — hero print, `上山聚义，共一百零八人。`, "Climb the mountain. Unite the 108."
2. **Subscribe band** — HSK level select + email + Subscribe → existing `POST /set_subs` (`src/set_subscriptions/app.py`, public, no authorizer).
3. **The story** — 108 outlaws, the 14th-century classic, the map of your year. Print right.
4. **Daily word** — the 每日一词 card (前面 / qián miàn) + three beats: word each morning → quiz next day → keep the streak, gather a hero.
5. **Levels** — HSK 1–6 picker with sample words → existing `GET /sample_vocab` (filtered to `Visibility: public`). Plus the upload-own-list action: new authed `POST /lists` in `src/create_list/`, implementing the CSV contract, derived fields, and caps specified in [User-created vocab lists](#user-created-vocab-lists-decisions). The schema it writes is fixed in Phase 0; this phase builds the endpoint and the UI against it.
6. **Heroes** — tiger print, one example hero card with an ability.
7. **Oath** — dark band, second subscribe, heroes-board visual (placeholder — see Open dependencies).

**Nav:** Home, Quiz, Review, Sign in (replacing `navBar.vue`).

---

## Phase 4 — Port the remaining screens

Thirteen routes exist today in `src/router.js`. Port each into the new design system, reusing the same endpoints:

| Route | Current view | Notes |
|---|---|---|
| `/quiz` | `Quiz.vue` (945 lines) | Largest file. Quiz is generated client-side from `GET /review`; results go to `POST /quizzes`. Split into components during the port. |
| `/review` | `Review.vue` | `xlsx` export — replace the pinned 0.15.6 (known CVEs). |
| `/history` | — (redirect) | `router.js:39-41` redirects to `/review`. No view to port, but carry the redirect into vue-router 4 so old email and external links keep working. |
| `/signin`, `/verification` | `SignIn.vue`, `SignInAnswerChallenge.vue` | Custom-auth OTP flow. |
| `/profile`, `/profile-settings` | `UserProfile.vue`, `EditUserInfo.vue` | Profile becomes the natural home for progression in Phase 6. |
| `/manage-lists` | `ManageLists.vue` | |
| `/sentences` | `UserSentences.vue` | Its `GET history` call targets an endpoint that does not exist — repoint to `/review`. |
| `/unsub`, `/subscribed` | `Unsubscribe.vue`, `SignUpConfirmation.vue` | |
| `/my-quizzes` | `UserQuiz.vue` | 52-line unlinked stub — fold into the progression work rather than porting. |

**Cutover:** deploy to `staging.haohaotiantian.com` (bucket + distribution `E14R2YU4CYXBZG`), verify against the screenshot set, then promote. Note the workflow's CloudFront invalidation only busts `/index.html` and `/app.js`; Vite's hashed filenames differ from Vue CLI's — **update the invalidation paths or the cutover will serve stale assets.**

---

## Phase 5 — Email redesign

The daily email is the primary product surface and must not look like the old site.

- Rework `src/send_daily_email/email_template.html` and `word_template.html` into the new visual language — within email-client constraints: tables, inline styles, no custom fonts (fall back to system serif for Chinese), no CSS variables.
- **Drop the two hardcoded list assumptions in `assemble_word_html_content`.** Line 187 branches on literal list names (`'HSK Level 1'…`) to choose the example-sentence site, and line 197 derives the level as `subscription.list_name[-1]` — which yields `"t"` for a list called "My list". Both are marked "before list database refactor" in the code; Phase 0 supplies the metadata to replace them, and a user list makes them wrong rather than merely ugly.
- Private-list quiz/review links point at the authed path and require sign-in — see decision 2 in [User-created vocab lists](#user-created-vocab-lists-decisions).
- Respect the new `Language preference` when rendering chrome.
- Once Phase 6 lands, add streak/provisions/next-hero lines to the email.

---

## Phase 6 — Progression primitives

There is **no streak, no aggregate stats, and no rollup anywhere today**. Everything is computed on the fly. This phase adds the first persisted progression state.

**New DynamoDB items** (same single table, `PK`/`SK`, GSI1):

| Item | PK | SK |
|---|---|---|
| User progression | `USER#<sub>` | `PROGRESS` |
| User's hero slot | `USER#<sub>` | `HERO#<rank:03d>` |
| Hero catalog (global) | `HERO#<hero_id>` | `METADATA` |

`PROGRESS` holds: `current_streak`, `longest_streak`, `last_practice_date`, `words_seen`, `heroes_gathered`, `provisions`, `next_hero_rank`, `reveal_stage`.

**Give `PROGRESS` GSI1 keys** (`GSI1PK: 'USER'`, `GSI1SK: 'USER#<sub>#PROGRESS'`). `query_all_users` reads **GSI1**, not the base table (`user_service.py:66-70`), so it only returns items that carry a `GSI1PK` — metadata and subscriptions today. Without GSI1 keys, `PROGRESS` never appears in the daily loop and the "free fan-out" below silently costs an extra `GetItem` per user per day. Projection is already `ALL` (`template.yaml:504-505`), so no index change is needed.

**Define what a "day" is before writing `reconcile`.** Injectable time (see Rollout §3) settles *how* the date gets in, not *which* date it is. Today `set_quiz_results/app.py:20` and `set_sentence/app.py:21` stamp `datetime.now()` in a Lambda — i.e. **UTC** — and the daily job runs `cron(0 20 * * ? *)`, so a subscriber in Asia receives the mail at ~4am the following local day. Streaks against a global subscriber base need an explicit answer: UTC day, per-user timezone, or a day boundary anchored to send time. Per-user timezone means a new user attribute and a `reconcile` that takes the user's zone; UTC is simpler and defensible if the UI says so. Pick one — it also determines what the retroactive backfill computes.

**Recommended architecture — reconcile lazily, not on a fan-out schedule.** Put the whole state machine in one new layer module `src/layer/python/progression_service.py` with a pure `reconcile(progress, today)` function, and call it from two places:

- `src/set_quiz_results/app.py` — on practice, advance streak and reveal stage.
- `src/send_daily_email/app.py` — which **already loops over every user daily** via `user_service.query_all_users()`. Reconciling there is free fan-out: no new scheduled job, and the email reflects truth. This depends on the Phase 0 pagination fix: unpaginated, that query stops at 1MB and progression would silently freeze for every user past the cap.

Make it idempotent by date so a lazy call on `GET /progress` can also catch up a user who has not been emailed yet. A pure function over `(progress, today)` is straightforwardly unit-testable with the existing pytest + moto setup.

**Nice property to lean on:** 108 heroes ÷ ~365 days ≈ one hero per 3.4 days, and each hero has 3–4 reveal stages. So **one reveal stage per qualifying practice day** produces the full 108 in a year with no separate pacing logic. The reveal *is* the progress bar, exactly as the brief describes.

**Provisions:** capped at 3–4 on `PROGRESS`. A missed day spends one instead of breaking the streak. Framed as heroes eating from the stores — never as purchased forgiveness, per the brief.

**New endpoints:** `GET /progress` (Cognito auth). Frontend: week strip showing quizzes done — note `dailyQuizzes.vue` already contains this grid fully written but **commented out at lines 15–26, with its CSS intact**. Reuse that markup rather than rebuilding it.

---

## Phase 7 — Collection layer

**Hero catalog schema** (`HERO#<hero_id>` / `METADATA`): `rank` (1–108), `tier` (`heavenly` for the 36 天罡 / `earthly` for the 72 地煞), `name_simplified`, `name_traditional`, `pinyin`, `name_english`, `nickname_*` (same four fields), `rumour`, `story`, `arrival_line`, `weapon`, `portrait_key`, `ability`.

Ship a **seed loader** plus a JSON seed file, and populate only the four heroes named in the brief — 鲁智深 Lu Zhishen "Flowery Monk", 武松 Wu Song "Pilgrim", 李逵 Li Kui "Black Whirlwind", and one Earthly Fiend for the compact treatment — so the mechanics are fully playable and testable before the other 104 exist. Model `models.py` `Hero` and `HeroSlot` dataclasses alongside the existing `Word` / `Quiz` / `Sentence`.

**Screens** (mobile-first, per the brief's priority order):

1. **Stone tablet 石碣** — 108 slots, countable from session one. Unearned = silhouette, never blank. Next hero glows. The 36/72 tier split must read **without a text label**. Departed heroes grey out but stay named. Mock near-empty, ~40-with-one-departed, and complete. The 108-on-a-phone navigation question (scroll / zoom / sectioned) is still open.
2. **Hero card** — four reveal states: silhouette+weapon → nickname → rumour → full card. Heavenly Spirits get richer treatment incl. audio for their arrival line; Earthly Fiends compact. Plus the departure state — melancholy, not punishment.
3. **Provisions** — inventory full/low/empty, the auto-spend notification, and the 聚义 day marker for practising all three types in one day (the warmest moment in the app).

**Audio for arrival lines:** reuse the existing Step Functions pipeline — `GenerateAudioStateMachine`, `src/get_chars_for_list_id/app.py`, Polly `Zhiyu`, mp3s to `vocab-audio-${Stage}`. Generalise `get_chars_for_list_id` to accept hero text rather than writing a second pipeline.

**Rule set is undefined.** Ability mechanics (e.g. 倍力 doubling one quiz score a week) are illustrative only in the design notes. Treat abilities as **display-only metadata in this phase** and specify the actual rules as a separate exercise — building a rule engine against illustrative examples will produce the wrong engine.

---

## Rollout and isolation strategy (applies to Phases 6–8)

Phases 0–5 are a normal staging → prod cutover: a visual redesign with no behavioural change, verifiable against the current-state screenshot set. **Only the progression and collection layers need the machinery below.** Keeping that boundary sharp is what makes the redesign shippable without waiting on the risky part.

### No third AWS environment

`vocab-staging` already has its own Cognito pool and its own DynamoDB table, so it has **no real subscribers and no real word history**. A `vocab-beta` stack would inherit exactly that gap. Progression is a *time-based* mechanic — streaks, ~3.4-day hero reveals, a year-long arc — so it cannot be evaluated on an account with no history, in any environment. A third stack adds ops and cost without answering the question. Use a beta cohort on prod instead.

### 1. Per-user feature flag

Add a `Feature flags` string set to the existing user metadata item (`USER#<sub>` / `USER#<sub>`). No new table and no flag service — it rides along in the query `user_service.query_single_user` already makes, and `_format_user_data` populates it onto the `User` dataclass — via `.get('Feature flags', set())`, since no existing record has the attribute.

> DynamoDB string sets **cannot be empty**. Removing a user's last flag must be a `REMOVE` on the attribute, not a write of an empty set — otherwise un-flagging a tester fails with a validation error. If that edge is annoying, a plain list is the simpler type here; the set buys nothing at this size.

- **Backend gates:** `progression_service.reconcile()` is a no-op for unflagged users; `GET /progress` returns empty; `SendDailyEmail` omits the hero block.
- **Frontend gates:** tablet/heroes routes and nav entries hidden unless `GET /user` returns the flag.
- **Setting it:** a small admin script writing directly to the table. Do not build UI for this.

Testers get the feature on their **real accounts, with real streak history and real daily emails** — the only setup in which the mechanic can actually be judged. Note the beta UI ships inside the same public S3/CloudFront bundle and is readable by anyone who opens the JS; that is fine here (no secrets), but it means the flag is a product gate, not a security boundary.

### 2. Harden the daily email loop

`SendDailyEmail` iterates every user once a day and has `MaximumRetryAttempts: 0`. An unguarded exception in progression code means **nobody gets email that day, with no retry** — this is the largest blast radius in the system, and it is larger than anything a separate environment protects against. Wrap the per-user progression call in `try/except` so a progression failure degrades to "no hero block in this email" rather than "no email." Log and alarm on it via the existing CloudWatch `Error` metric filter.

### 3. Injectable time

`reconcile(progress, today)` must take `today` as a parameter and never call `datetime.today()` internally. This single constraint is the highest-leverage decision in the collection layer:

- Unit tests replay a simulated year in milliseconds.
- A replay script can fast-forward a seeded staging account through 90 days of scenarios — missed days, provision depletion, hero completion, departure — without waiting.
- The same pure function serves both the `set_quiz_results` call path and the `SendDailyEmail` reconcile.

### 4. Split Phase 7 into two releases

- **7a — mechanics behind the flag.** Deploy dark to prod. Beta cohort only. Run it for several weeks of genuine daily use; the four-hero seed is enough to exercise every state.
- **7b — GA.** Remove the gate once the mechanic and the hero content are both ready.

**You do not need to run progression early for everyone to have a streak at launch.** Every quiz is already persisted as `USER#<sub>` / `DATE#<date>#QUIZ#<id>` with its date — streaks and words-seen are **derivable retroactively** from history that already exists. Write a one-off backfill that replays each user's quiz items through the same pure `reconcile()` function, and everyone gets a correct streak on day one of GA. This is why the beta cohort can stay genuinely small.

### Rollback

Progression items are additive under new SK prefixes and never mutate existing items, so rollback is: clear the flag (feature disappears immediately, no deploy), then optionally delete `PROGRESS` and `HERO#` items. No migration to reverse.

---

## Phase 8 — Intro sequence

Three or four skippable onboarding screens: the premise (~1120, corrupt Northern Song, 108 outlaws) → 逼上梁山 "driven to Liangshan" → the 108 and their ranks, with one example card so the reward format is legible before anything is earned → 聚义. Needs a way to carry narrative without a wall of exposition, and illustration or motif per screen.

---

## Hero mechanics — open design questions

*This section is the starting point for a separate design pass. Everything here is undecided; the rest of the plan is deliberately built so these answers can change without invalidating it.*

**What is already settled (constraints any rule set must satisfy):**

- Rewards are **decoupled from proficiency** — a beginner and an advanced learner unlock the same heroes on the same schedule. Nothing may imply a difficulty ladder.
- Heroes are **never permanently losable**. Setbacks slow you down; they never close a door. Departure reads as melancholy, not punishment.
- 108 heroes ÷ ~365 days ≈ one hero per 3.4 days, and each hero has 3–4 reveal stages — so **one reveal stage per qualifying practice day** yields the full 108 in a year with no separate pacing logic. The reveal *is* the progress bar.
- The state machine must be a **pure function** `reconcile(progress, today)` (see Rollout §3), so any rule set must be expressible as a deterministic transition over stored state plus a date.

**Open questions:**

1. **What counts as a "qualifying practice day"?** A completed quiz? Reading the daily word? Writing a sentence? The 聚义 marker rewards "all three types in one day," which implies three tracked activity types — but only quizzes (`POST /quizzes`) and sentences (`POST /sentences`) are currently recorded. Reading the daily word has no event at all. **If a third type is required, it needs a new tracked event.**
2. **Provisions economy.** Cap is 3–4. How are they *earned* — one per 聚义 day, per streak milestone, passively? What's the accrual rate relative to the burn rate? This is the balance question that determines whether a lapse feels forgiving or trivial.
3. **Departure threshold.** How long a lapse, after provisions are exhausted, before a hero departs? Do they return, and on what condition? "Never permanently losable" implies a return path exists — it needs defining.
4. **Ability rule set.** Currently illustrative only (e.g. 倍力, doubles one quiz score a week). Abilities are **display-only metadata in Phase 7a** by design — building a rule engine against illustrative examples produces the wrong engine. Open: are abilities passive or activated? Do they stack? Are they per-hero or per-tier? Does an ability's effect touch quiz scoring (which would couple rewards back to proficiency — see constraint 1, and be careful here).
5. **Tier pacing.** 36 Heavenly / 72 Earthly. Are they interleaved across the year, or does tier correlate with when a hero arrives? The canonical reordering ceremony at 忠义堂 happens at 108, which suggests arrival order need not match rank.
6. **Onboarding cold start.** Day 1 shows 108 empty slots. How many days until the first *full* hero card, given a 3–4 stage reveal? If it's four days before any payoff, the intro sequence has to carry a lot of weight.

**Where to pick this up:** the schema in Phase 7 (`HERO#<hero_id>` / `METADATA`, `USER#<sub>` / `HERO#<rank>`, `PROGRESS`) is deliberately generous — reveal stage, status, and provisions are all stored fields, so most rule changes are logic-only and require no migration.

---

## Open dependencies (not solvable in code)

- **108 hero portraits** — the single largest content dependency and the critical path for Phase 7. Phase 7's four-hero seed exists specifically so engineering is not blocked on it.
- **Woodblock prints** in `assets/` are stand-ins for licensed or original artwork.
- **Heroes-board visual** (home section 7) is a placeholder needing real art or a defined layout.
- **Ability rule set** — undefined, see Phase 7.
- **Hero text for all 108** — names, nicknames, rumours, stories, arrival lines.

---

## Verification

**Backend** — `pytest` from the repo root (needs the local `.venv`; `conftest.py` sets `pythonpath = src, src/layer/python, src/user_pool_triggers` and moto mocks AWS). Coverage floor is 70%. New progression logic should be tested as a pure function over `(progress, today)` across: unbroken streak, one missed day with provisions, missed day without provisions, hero completion, and departure after a long lapse.

**Progression time-travel** — because `today` is injected, add a test that replays a full simulated year day by day and asserts the invariants: 108 heroes reached, provisions never negative or above cap, no hero ever permanently lost. Add a companion replay script that drives a seeded staging account through the same sequence against real DynamoDB, so the API and UI are exercised end-to-end without waiting on the calendar.

**Email failure isolation** — test that a progression exception for one user does not prevent the daily send for that user or any other. This is the highest-blast-radius path in the system. Cover the same isolation for the Phase 0 `KeyError`: a user subscribed to a list with no word for today must degrade to "that list omitted from their email," not "no email for anyone."

**User lists** — unit-test the upload path against `src/tests/unit/example_words_list.csv` and a fixture missing the optional columns: derived `Traditional` and `Pinyin` land on the item, `Audio file key` and `HSK Level` are `""`, and over-cap uploads are rejected rather than truncated. Assert `sample_vocab` and the public `GET /review` return **no** `Visibility: private` list, and that the authed path 403s a caller who is not the owner. Existing moto-based tests (`test_sample_vocab.py`, `test_get_review_words.py`, `test_set_todays_words.py`) already seed lists and extend naturally.

**Pagination** — seed enough users past the 1MB GSI1 page to prove `query_all_users` returns all of them; the failure mode this guards is silent, so an assertion on count is the only thing that catches it.

**Backend integration** — `sam build && sam deploy` to the `vocab-staging` stack via the existing `.github/workflows/deploy.yml` (push to `staging`). Verify the daily pipeline by manually invoking `SetTodaysWords` and confirming `SendDailyEmail` fires off the `todays-words-set` EventBridge event, including on an announcement day (the Phase 0 fix).

**Frontend** — `npm run dev` locally against `api.staging.haohaotiantian.com`. Vitest for the i18n store and progression display logic. Drive the staging site at 390 and 1120 widths and diff against the current-state screenshot set to confirm no functional regression in the port.

**Email** — render both templates to a file and check in a real client before deploying; the daily send has `MaximumRetryAttempts: 0`, so a template error means that day's email is simply lost.

---

## Sequencing summary

```
Phase 0  backend hygiene ──┬─→ Phase 1 scaffold ─→ Phase 2 i18n ─→ Phase 3 home ─→ Phase 4 port ─→ CUTOVER
                           │                                                                          │
                           └──────────────────────────────────────────────→ Phase 5 email ───────────┤
                                                                                                      │
                          ┌───────────────────────────────────────────────────────────────────────────┘
                          │
                          └─→ Phase 6 progression ─→ Phase 7a mechanics ─→ [BETA COHORT, weeks of real use]
                                                                                    │
                                                     Phase 8 intro ─→ Phase 7b GA ──┘
                                                                       + retroactive streak backfill
```

Phases 0–4 ship the redesigned bilingual site as a complete deliverable, on a normal staging → prod cutover. Phase 5 can run in parallel once the design system exists. Phases 6–8 are the collection layer: they deploy to prod dark behind a per-user flag, soak with a small beta cohort on real accounts, and go GA only once both the mechanic and the hero content are ready. The redesign never waits on the collection layer.
