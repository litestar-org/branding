<p align="center">
  <img src="assets/Branding - SVG - Transparent/Logo - Banner - Inline - Light.svg#gh-light-mode-only" alt="Starlite Logo - Light" width="100%" height="auto" />
  <img src="assets/Branding - SVG - Transparent/Logo - Banner - Inline - Dark.svg#gh-dark-mode-only" alt="Starlite Logo - Dark" width="100%" height="auto" />
</p>

# Branding
This repository contains all assets, artwork and graphics used by [@litestar-org](https://github.com/litestar-org/) projects.

## Color Palette

### Primary Colors:
* ![#202235](https://placehold.co/15x15/202235/202235.png) `#202235`
* ![#EDB641](https://placehold.co/15x15/EDB641/EDB641.png) `#EDB641`

### Secondary Colors
* ![#FFD480](https://placehold.co/15x15/FFD480/FFD480.png) `#FFD480`
* ![#DCDFE4](https://placehold.co/15x15/DCDFE4/DCDFE4.png) `#DCDFE4`
* ![#ffffff](https://placehold.co/15x15/ffffff/ffffff.png) `#ffffff`

## Guidelines
View the [brand guidelines](assets/Litestar%20Brand%20Guidelines.pdf) for detailed information.

![Litestar Brand Guidelines](https://github.com/starlite-api/branding/blob/main/assets/Litestar%20Brand%20Guidelines.svg)

## Ecosystem Branding Pack (`assets/projects/`)

Full per-project vector (`svg/`), multi-resolution raster (`png/`), inline README banners (`banners/`), and favicon suites (`favicons/`) for all 22 Litestar ecosystem packages live under [`assets/projects/`](assets/projects/README.md):

- **Core & Standalone Libraries**: [`litestar`](assets/projects/litestar), [`sqlspec`](assets/projects/sqlspec), [`advanced-alchemy`](assets/projects/advanced-alchemy), [`pytest-databases`](assets/projects/pytest-databases), [`polyfactory`](assets/projects/polyfactory), [`dtos`](assets/projects/dtos), [`type-lens`](assets/projects/type-lens), [`flow`](assets/projects/flow)
- **Plugins & Tooling**: [`debug-toolbar`](assets/projects/debug-toolbar), [`litestar-ai`](assets/projects/litestar-ai), [`litestar-skills`](assets/projects/litestar-skills), [`litestar-asyncpg`](assets/projects/litestar-asyncpg), [`litestar-oracledb`](assets/projects/litestar-oracledb), [`litestar-vite`](assets/projects/litestar-vite), [`litestar-granian`](assets/projects/litestar-granian), [`litestar-mcp`](assets/projects/litestar-mcp), [`litestar-queues`](assets/projects/litestar-queues), [`litestar-saq`](assets/projects/litestar-saq), [`litestar-security`](assets/projects/litestar-security), [`litestar-autowire`](assets/projects/litestar-autowire), [`litestar-email`](assets/projects/litestar-email), [`litestar-htmx`](assets/projects/litestar-htmx)

To regenerate all project packs and inline banners:

```bash
uv run python tools/generate_branding_pack.py
```
