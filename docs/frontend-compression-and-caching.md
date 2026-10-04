# Frontend Compression and Caching

## Purpose

This guide describes how production compression, cache headers, and GeoJSON versioning apply to the frontend. These concerns span three layers:

| Concern                                       | Owner                   |
| --------------------------------------------- | ----------------------- |
| Generate and sanitize street data             | `main.py`               |
| Fingerprint frontend assets                   | Vite                    |
| Compress responses and set HTTP cache headers | Hosting platform or CDN |

Compression and HTTP cache headers do not belong in `main.py`. The data pipeline should produce normal GeoJSON. The server that delivers the built site decides whether to use Brotli or gzip and which `Cache-Control` header to send.

## Current deployment

`.github/workflows/static.yml` builds `frontend/dist` and deploys it through GitHub Pages. The workflow does not run `main.py`; generated frontend data must already exist before the frontend build starts.

Vite fingerprints bundled files automatically, producing names such as:

```text
assets/index-D4m8YNj1.js
assets/vendor-maplibre-DUgkNhpu.js
assets/maplibre-gl-worker-CRiIRpYb.js
```

`main.py`, however, copies GeoJSON into `frontend/public/data` with stable names:

```text
data/somerville_streets.geojson
data/cambridge_streets.geojson
```

Vite copies files from `public/` without adding a content hash.

## GitHub Pages behavior

At the time this guide was written, the deployed site's existing JavaScript and CSS responses included:

```http
Content-Encoding: gzip
Cache-Control: max-age=600
Vary: Accept-Encoding
```

GitHub Pages controls those headers. It does not provide repository-level configuration for arbitrary response headers, so adding `_headers`, `.htaccess`, or header directives to the Pages artifact will not create a one-year immutable cache policy. The current Pages deployment also provides no project-level control over choosing Brotli instead of gzip.

Do not generate `.gz` or `.br` siblings in `main.py`. Precompressed files work only when a server performs content negotiation and sends the correct `Content-Encoding`. Without that server configuration, a browser may receive compressed bytes as an ordinary file instead of decoded GeoJSON.

## Verify the deployed responses

Run these checks after each hosting or deployment change. Use a GET request with the body discarded rather than assuming that a host treats `HEAD` identically.

### GeoJSON

```bash
curl -sS -D - -o /dev/null --compressed \
  https://dustinmichels.github.io/bike-stress-model/data/somerville_streets.geojson
```

Expected headers:

```http
HTTP/2 200
Content-Encoding: gzip
Vary: Accept-Encoding
Content-Type: application/geo+json
Cache-Control: max-age=600
```

The current public deployment predates these GeoJSON files, so this response must be checked after the updated frontend is deployed.

### Hashed JavaScript

Copy a current asset URL from the deployed `index.html`, then run:

```bash
curl -sS -D - -o /dev/null --compressed \
  https://dustinmichels.github.io/bike-stress-model/assets/index-REPLACE_WITH_HASH.js
```

Check the following:

- `Content-Encoding` is `gzip` or `br`.
- `Vary` includes `Accept-Encoding`.
- `Content-Type` matches the asset.
- `Cache-Control` matches the hosting policy.

The GeoJSON files are approximately 0.61–1.41 MiB uncompressed and 72–182 KB with gzip. Compression therefore matters more than changing the GeoJSON data format at the current dataset size.

## If GitHub Pages does not compress `.geojson`

GitHub Pages chooses compression based on its own serving behavior and MIME handling. If the deployed GeoJSON response has no `Content-Encoding`, publish the same content with a `.json` extension and verify again.

Keep the generated backend artifact as `.geojson`; only rename the frontend copy. The relevant change would be in the copy step in `main.py`:

```python
source_filename = f"{place.slug}_streets.geojson"
frontend_filename = f"{place.slug}_streets.json"
```

The frontend map must then reference `.json`:

```typescript
export const CITY_FILE_MAP: Record<string, string> = {
  Somerville: 'somerville_streets.json',
  Cambridge: 'cambridge_streets.json',
  Everett: 'everett_streets.json',
  Malden: 'malden_streets.json',
}
```

This is the only compression-related case that should affect `main.py`, and it changes the frontend filename rather than performing compression itself.

## Immutable caching requires versioned URLs

Never assign a one-year immutable cache policy to the current stable URL:

```text
data/somerville_streets.geojson
```

If that URL is cached as immutable, clients can continue using stale street data after the file changes. Immutable caching is safe only when a content change also changes the URL.

### Recommended versioning: Vite URL imports

If the site moves to a host that supports custom cache headers, let Vite fingerprint the GeoJSON rather than implementing hashing and a manifest in Python.

1. Change the frontend copy destination in `main.py`:

   ```python
   dest_dir: str = "frontend/src/assets/data"
   ```

2. Import each dataset as a URL in `frontend/src/composables/useBikeModel.ts`:

   ```typescript
   import cambridgeUrl from '@/assets/data/cambridge_streets.geojson?url'
   import everettUrl from '@/assets/data/everett_streets.geojson?url'
   import maldenUrl from '@/assets/data/malden_streets.geojson?url'
   import somervilleUrl from '@/assets/data/somerville_streets.geojson?url'

   export const CITY_FILE_MAP: Record<string, string> = {
     Somerville: somervilleUrl,
     Cambridge: cambridgeUrl,
     Everett: everettUrl,
     Malden: maldenUrl,
   }
   ```

3. Fetch the imported URL directly:

   ```typescript
   const response = await fetch(fileName, {
     signal: controller.signal,
   })
   ```

Vite will emit each file with a content hash. The selected city is still downloaded only when `fetch()` requests its URL; statically importing the URLs does not inline or eagerly download these datasets.

## Cache policy on a configurable host

On Cloudflare Pages, Netlify, S3/CloudFront, or another host with response-header controls, use policies equivalent to:

```text
/assets/*
  Cache-Control: public, max-age=31536000, immutable

/index.html
  Cache-Control: no-cache
```

This works because Vite assets, including GeoJSON imported with `?url`, receive content-hashed filenames. `index.html` must remain revalidatable so it can point clients to the newest hashed assets.

If GeoJSON keeps stable `/data/*.geojson` names, use a short cache lifetime instead:

```text
/data/*
  Cache-Control: public, max-age=600, must-revalidate
```

Header-file syntax differs by host. Configure these rules in the hosting configuration, not in `main.py`.

## Recommended path

For the current GitHub Pages deployment:

1. Keep normal, uncompressed GeoJSON output in `main.py`.
2. Deploy the current frontend.
3. Verify the GeoJSON response with `curl --compressed`.
4. If `.geojson` is not compressed, publish the frontend copy as `.json` and verify again.
5. Accept GitHub Pages' cache policy while the site remains on Pages.

If long-lived immutable caching becomes a requirement:

1. Move to, or proxy through, a host with custom response-header controls.
2. Move frontend datasets into Vite's asset graph and import them with `?url`.
3. Apply immutable caching only to fingerprinted `/assets/*` URLs.
4. Keep `index.html` short-lived or revalidated.

## References

- [Vite static asset handling and explicit `?url` imports](https://vite.dev/guide/assets.html#explicit-url-imports)
- [GitHub Pages custom deployment workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [GitHub community discussion: custom headers on Pages](https://github.com/orgs/community/discussions/54257)
