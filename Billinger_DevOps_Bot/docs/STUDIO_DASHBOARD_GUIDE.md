# Billinger Bot v2.6.0 — Studio Dashboard Guide

## Design direction

The v2.5 interface is an original offline design inspired by the visual language of premium creative-studio websites:

- Architectural off-white gallery space
- Oversized condensed editorial typography
- Coral-red three-dimensional title treatment
- Framed dark capability exhibit
- Scroll-guided homepage narrative
- Full-screen indexed navigation drawer
- Large whitespace and restrained borders
- Subtle pointer, reveal, tilt and marquee motion

No source code, fonts, photographs, videos, logos, illustrations, or proprietary assets were copied from the reference website.

## Lightweight implementation

The visual layer consists of one local CSS file and a small JavaScript enhancement in the existing application. It uses:

- CSS gradients and transforms
- CSS perspective and shadows
- IntersectionObserver for reveal motion
- A local pointer halo on precise-pointer devices
- Reduced-motion fallbacks

It does not use WebGL, Three.js, Electron, remote fonts, video backgrounds, a game engine, or a dedicated GPU.

## Navigation

Select **Menu** in the top-left corner to open the full studio index. The drawer:

- Scrolls independently at every supported screen height
- Closes through the close button, backdrop, Escape key, or selected page
- Preserves all v2.4 pages and functions
- Expands to full width on small mobile screens

## Homepage

The homepage introduces the complete learner journey:

1. Learn from verified technical materials.
2. Practice through labs and company simulations.
3. Prove capability through examinations and capstones.
4. Build a verified portfolio.
5. Match and apply for suitable roles.
6. Prepare for job-specific interviews.

## Accessibility and performance

- Keyboard-accessible navigation and controls
- Visible focus styling on inputs
- `prefers-reduced-motion` support
- No mandatory network assets
- No visual dependency that blocks core workflows
- Responsive desktop, laptop, tablet and mobile layouts
