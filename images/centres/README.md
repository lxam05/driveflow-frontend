# Test centre SEO images

One folder per driving test centre. Folder names match the page slug:

| Folder | Page |
|--------|------|
| `ballina/` | `/ballina-routes.html` |
| `naas/` | `/naas-routes.html` |
| `birr-county-arms-hotel/` | `/birr-county-arms-hotel-routes.html` |

## How to add an image

1. Drop the file into the matching centre folder, e.g. `images/centres/ballina/about.jpg`
2. Tell the agent which centre + filename + where on the page it should go
3. Do **not** paste images into shared files (`shared.js`, `shared.css`) unless every centre should get the same asset

## Suggested naming

Use short, descriptive filenames (lowercase, hyphens). Prefer including the centre slug for SEO:

- `dun-laoghaire-rsa-driving-test-centre-building.webp` — hero / building
- `dun-laoghaire-driving-test-centre-entrance-bakers-point.webp` — entrance
- `dun-laoghaire-driving-test-centre-exit-bakers-point.webp` — exit
- `og.jpg` — social share / Open Graph (1200×630 if possible)

Convert large phone PNGs to compressed **WebP** before wiring into HTML.

Public URL once deployed:

`https://www.driveflow.ie/images/centres/{slug}/{filename}`

## Notes

- Pages are edited one centre at a time; empty folders are intentional until images arrive.
- Prefer WebP or compressed JPG; keep file sizes reasonable for page speed.
- Alt text should name the centre and what the photo shows (set when the image is wired into the HTML).
