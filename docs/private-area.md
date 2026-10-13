# The private area: a runbook for the owner

The site has one area behind a login, at `/private`. Its content is not in this repository and is not in the
site's build. It lives in a separate private repository as a bundle of JSON files, and the site fetches a file
only when a signed-in reader asks for a page. Until the four settings below are present, every address under
`/private`, the login included, answers "not found".

## Set it up, once

1. **Make the private store.** Create a new private repository on GitHub. It will hold only the bundle.
2. **Make a read-only token for it.** In GitHub: Settings, Developer settings, Fine-grained tokens. Give the token
   access to that one repository only, with "Contents: Read-only" and nothing else. Give it an expiry date and note
   the date.
3. **Make a long password** in a password manager: at least five random words or twenty random characters. The
   site does not slow down repeated guesses, so the length of the password is the defence.
4. **Hash the password in your own terminal.** Copy the password, then, from the repository:

   ```
   pbpaste | node web/scripts/private-hash.mjs
   ```

   It prints one line, `<salt>:<hash>`. The script reads the password from standard input so that it is never
   written into the shell's history. On a machine without `pbpaste`, run `node web/scripts/private-hash.mjs`,
   paste the password, press Enter and then Ctrl-D.
5. **Make a session secret**: `openssl rand -hex 32`.
6. **Set four values in Vercel**, under the project's Settings, Environment Variables:

   | Name | Value |
   | --- | --- |
   | `PRIVATE_PASSWORD_HASH` | the line the hashing script printed |
   | `PRIVATE_SESSION_SECRET` | the line `openssl` printed |
   | `PRIVATE_CONTENT_REPO` | the private repository, as `owner/name` |
   | `PRIVATE_CONTENT_TOKEN` | the read-only token |

   Tick **Production only** and mark each one **Sensitive**. **Do not tick Preview: every pull request gets a
   preview link, and with these values set there the private area would be live on every one of them.** Leave
   Development unticked as well.
7. **Redeploy** production, since settings reach only a new deployment.

## Publish or update the content

1. Keep the source documents and a `bundle.yaml` in a folder outside this repository. The top of
   `scripts/private_bundle.py` shows the shape of the spec: sections, and for each document a slug, a title, a
   kind (`doc` for markdown, `table` for a CSV) and its source file; a table also lists its columns and the
   columns to filter by.
2. Clone the private repository somewhere outside this one, then run, from this repository:

   ```
   uv run python scripts/private_bundle.py <source folder> <clone of the private repository>
   ```

   The script refuses to write inside this repository.
3. Commit and push in the clone. The site keeps each file for a few minutes, so a change shows within about five.
   No deployment is needed.
4. A document removed from the spec leaves its old JSON file in the clone. Nothing links to it, but delete it
   there so the store holds only what the manifest lists.

## Add a second section later

Add another entry under `sections` in `bundle.yaml`, with its own slug, title and documents, run the bundler
again and push. The index at `/private` lists it; nothing in this repository changes.

## Rotate the password

Make a new password, hash it as above, replace `PRIVATE_PASSWORD_HASH` and replace `PRIVATE_SESSION_SECRET` with
a new random value, then redeploy. Replacing the session secret signs out every browser that is signed in;
replacing the hash alone would leave them signed in for up to thirty days.

## Rotate the token

Make a new fine-grained token with the same single read-only permission, replace `PRIVATE_CONTENT_TOKEN`,
redeploy, check that a page loads, then delete the old token in GitHub. If a page shows "could not be shown", the
token has expired or lost access: this is the first thing to check.

## Turn it off

Delete any one of the four values and redeploy. Every address under `/private` is then "not found" again.

## What is and is not protected

- Pages under `/private` are sent with "no-store" and "noindex", are in no sitemap, search index or menu, and are
  not named in `robots.txt`, which would advertise the address.
- The Ask panel does not appear there, because it sends the page's title to an outside service.
- A session lasts thirty days in the browser that signed in. There is one password and no list of who used it.
- Anyone who has the password, the token or access to the private repository can read everything.
