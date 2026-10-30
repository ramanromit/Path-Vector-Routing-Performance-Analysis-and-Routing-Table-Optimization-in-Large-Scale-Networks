---
name: Obsidian Utility Console
colors:
  surface: '#131315'
  surface-dim: '#131315'
  surface-bright: '#39393b'
  surface-container-lowest: '#0e0e10'
  surface-container-low: '#1c1b1d'
  surface-container: '#201f22'
  surface-container-high: '#2a2a2c'
  surface-container-highest: '#353437'
  on-surface: '#e5e1e4'
  on-surface-variant: '#c1c6d7'
  inverse-surface: '#e5e1e4'
  inverse-on-surface: '#313032'
  outline: '#8b90a0'
  outline-variant: '#414754'
  surface-tint: '#aec6ff'
  primary: '#aec6ff'
  on-primary: '#002e6b'
  primary-container: '#0070f3'
  on-primary-container: '#ffffff'
  inverse-primary: '#0059c5'
  secondary: '#c6c5cf'
  on-secondary: '#2f3038'
  secondary-container: '#4a4b53'
  on-secondary-container: '#bcbbc5'
  tertiary: '#ffb596'
  on-tertiary: '#581e00'
  tertiary-container: '#ca4e00'
  on-tertiary-container: '#fffeff'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#aec6ff'
  on-primary-fixed: '#001a43'
  on-primary-fixed-variant: '#004397'
  secondary-fixed: '#e3e1ec'
  secondary-fixed-dim: '#c6c5cf'
  on-secondary-fixed: '#1a1b22'
  on-secondary-fixed-variant: '#46464e'
  tertiary-fixed: '#ffdbcd'
  tertiary-fixed-dim: '#ffb596'
  on-tertiary-fixed: '#360f00'
  on-tertiary-fixed-variant: '#7d2d00'
  background: '#131315'
  on-background: '#e5e1e4'
  surface-variant: '#353437'
typography:
  headline-xl:
    fontFamily: Geist
    fontSize: 2.25rem
    fontWeight: '600'
    lineHeight: 2.75rem
    letterSpacing: -0.03em
  headline-xl-mobile:
    fontFamily: Geist
    fontSize: 1.75rem
    fontWeight: '600'
    lineHeight: 2.25rem
    letterSpacing: -0.025em
  headline-lg:
    fontFamily: Geist
    fontSize: 1.5rem
    fontWeight: '600'
    lineHeight: 2rem
    letterSpacing: -0.02em
  headline-sm:
    fontFamily: Geist
    fontSize: 1.125rem
    fontWeight: '500'
    lineHeight: 1.5rem
    letterSpacing: -0.015em
  body-lg:
    fontFamily: Geist
    fontSize: 0.9375rem
    fontWeight: '400'
    lineHeight: 1.375rem
    letterSpacing: -0.01em
  body-md:
    fontFamily: Geist
    fontSize: 0.875rem
    fontWeight: '400'
    lineHeight: 1.25rem
    letterSpacing: -0.005em
  body-sm:
    fontFamily: Geist
    fontSize: 0.75rem
    fontWeight: '400'
    lineHeight: 1rem
    letterSpacing: 0em
  code-md:
    fontFamily: Geist
    fontSize: 0.8125rem
    fontWeight: '400'
    lineHeight: 1.125rem
    letterSpacing: -0.01em
  label-md:
    fontFamily: Geist
    fontSize: 0.8125rem
    fontWeight: '500'
    lineHeight: 1rem
    letterSpacing: 0em
  label-sm:
    fontFamily: Geist
    fontSize: 0.6875rem
    fontWeight: '500'
    lineHeight: 0.875rem
    letterSpacing: 0.04em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-compact: 0.5rem
  margin: 1.5rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style

This design system delivers an uncompromised, mission-critical workspace built for infrastructure engineers, systems researchers, and telemetry operators. Its brand personality is hyper-disciplined, utilitarian, and exact. It dispenses with decorative frivolities, ambient lighting effects, and soft skeuomorphism in favor of structural clarity, density, and low-latency interaction.

The style unites modern developer-centric minimalism with industrial terminal efficiency. It relies on opaque neutral zinc planar tiers, razor-sharp 1px boundary lines, rigorous typographic alignment, and a singular, razor-sharp electric blue accent used exclusively for status affirmation, interactive focus, and critical operations. The resulting interface feels authoritative, focused, and indestructible under complex cognitive loads.

## Colors

The palette is strictly constructed around neutral monochromatic zinc surfaces counterbalanced by an exact electric blue primary `#0070F3`. Every color token serves a deterministic functional purpose; there are no decorative background washes or atmospheric gradients.

### Palette Architecture
- **Canvas (`#09090B` / zinc-950):** Deep, pure matte ground for viewport backdrops.
- **Surface Elevation 1 (`#121215` / zinc-900):** Solid, opaque base container for panels, sidebars, and workspaces.
- **Surface Elevation 2 (`#18181B` / zinc-850):** Solid ground for floating flyouts, contextual menus, and interactive rows.
- **Structural Borders (`#27272A` / zinc-800):** Default 1px structural dividing lines.
- **High-Contrast Borders (`#3F3F46` / zinc-700):** Hover-state outlines, active selections, and interactive thresholds.
- **Primary Accent (`#0070F3`):** High-saturation electric blue reserved strictly for primary execution hooks, key active indicator pills, and focus halos.
- **Text & Foreground:** `#FAFAFA` (zinc-50) for maximum-clarity data strings and headers; `#A1A1AA` (zinc-400) for structural labels; `#52525B` (zinc-600) for inactive identifiers and metadata delimiters.

## Typography

The typographic hierarchy relies entirely on `Geist` across all text tiers. Its geometry features neutral grotesque proportions optimized for developer tooling, dense information density, and screen legibility.

All numerical tables, telemetry metrics, and code references utilize tabular figures (`font-variant-numeric: tabular-nums;`) to eliminate horizontal jitter during live streaming data feeds. Titles and high-level headings apply tight negative letter spacing to preserve compactness. Metadata tags, badges, and section anchors employ uppercase micro-labels with extended tracking (+0.04em) to ensure immediate scanning across multi-panel layouts.

## Layout & Spacing

Layout geometry follows an explicit, high-density 4px base coordinate rhythm. Workspaces are configured around multi-pane split panes rather than loose page flows. Content conforms to strict visual grid panels separated by 1px hairline dividers.

- **Desktop (1024px+):** Fixed-width side rails (240px navigation, 320px telemetry inspection inspector) flanked by an infinitely flexible central command canvas. Workspaces leverage consistent gutters (`1rem`) and edge margins (`1.5rem`).
- **Data Densities:** Toolbars and lists utilize compact element gaps (`0.5rem`) to maximize visible information per vertical scroll height.
- **Mobile (<768px):** Collapses inspection sidebars into bottom modal sheets; gutter scales down to `0.5rem` and outer frame margins contract to `1rem`. Structural dividers take precedence over whitespace for element grouping.

## Elevation & Depth

This design system completely eliminates soft, diffuse blur dropshadows and translucent glassmorphism. Elevation is rendered purely through opaque tonal layering combined with crisp hairline borders:

1. **Base Layer (Elevation 0):** Canvas `#09090B`. Recessed elements, terminal outputs, and inactive data wells use this level.
2. **Structural Panels (Elevation 1):** Solid `#121215` bordered by a 1px `#27272A` outline. Used for cards, dashboards, data tables, and tree views.
3. **Floating Overlays & Modals (Elevation 2):** Solid `#18181B` bordered by 1px `#3F3F46`. Supported by an architectural, high-precision shadow: `0 4px 12px rgba(0, 0, 0, 0.6)`. Shadows are pitch-black, tight, and lack color tinting to preserve a clinical aesthetic.
4. **Interactive Focus:** Depicted via an exterior 1px or 2px `#0070F3` stroke with zero blur offset.

## Shapes

The interface embraces a compact, controlled shape language (`roundedness: 1`):

- **Inputs, Buttons, Badges, Tabs:** Scaled at `0.25rem` (4px). This creates clean, sharp visual edges that nest seamlessly within dense toolbars.
- **Panels, Dialogs, Cards:** Scaled at `0.375rem` to `0.5rem` (6px to 8px max).
- **Nested Corners:** Inner elements explicitly follow the mathematical nesting rule ($R_{\text{inner}} = R_{\text{outer}} - \text{padding}$) to eliminate visual warping inside framed containers.
- **Data Indicators:** Exact circles or precise 2px square status markers for terminal-like telemetry.

## Components

### Buttons
- **Primary:** Solid `#0070F3` background, `#FFFFFF` text, `0.25rem` corner radius, font weight 500. Hover state: `#0060DF`. Active state: `#0050BF`.
- **Secondary / Ghost:** Surface `#18181B`, 1px border `#27272A`, `#FAFAFA` text. Hover state: border transitions to `#3F3F46` with background `#27272A`.
- **Destructive:** 1px border `#7F1D1D`, text `#EF4444`, surface transparent. Hover: background `#450A0A`.

### Inputs & Search Bars
- Background `#09090B`, 1px solid border `#27272A`, height `2rem` (32px) for high density.
- Text `#FAFAFA`, placeholder `#52525B`.
- Focus state: border color `#0070F3`, no ambient glow ring, sharp 1px internal inset or outline.
- Monospace keyboard shortcut indicators (`⌘K`) anchored to right padding in `#52525B`.

### Data Tables & Telemetry Lists
- Table header: `#121215`, text `#71717A`, uppercase micro-label, bottom border 1px `#27272A`.
- Rows: solid `#09090B` or `#121215`, row height 36px. Border-bottom 1px `#18181B`.
- Row hover: `#18181B` flat background shift.
- Numbers, timestamps, and hashes rendered in tabular numeric formatting with zero letter displacement.

### Chips & Badges
- Height 20px, radius `0.25rem`, padding `0 6px`.
- Solid `#18181B` surface with 1px border `#27272A`.
- Active / Status variant: 4px solid dot indicator in `#0070F3` (active/running), `#10B981` (healthy), or `#EF4444` (critical error) paired with `#FAFAFA` label text.

### Checkboxes & Switches
- Checkboxes: 14px by 14px, radius 3px, border 1px `#3F3F46`, background `#09090B`. Checked state: background `#0070F3`, border `#0070F3`, crisp `#FFFFFF` tick icon.
- Toggles: 28px width, 16px height, track `#27272A`. Thumb 12px `#FAFAFA`. Active track `#0070F3`.

### Cards & Panels
- Rigid `#121215` opaque background, hairline 1px `#27272A` perimeter, `0.375rem` radius.
- Headers separated from content sections via continuous 1px `#27272A` horizontal rules rather than floating whitespace blocks.