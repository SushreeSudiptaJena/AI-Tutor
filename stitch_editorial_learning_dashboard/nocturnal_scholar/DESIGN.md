---
name: Nocturnal Scholar
colors:
  surface: '#121414'
  surface-dim: '#121414'
  surface-bright: '#38393a'
  surface-container-lowest: '#0c0f0f'
  surface-container-low: '#1a1c1c'
  surface-container: '#1e2020'
  surface-container-high: '#282a2b'
  surface-container-highest: '#333535'
  on-surface: '#e2e2e2'
  on-surface-variant: '#c3c7ca'
  inverse-surface: '#e2e2e2'
  inverse-on-surface: '#2f3131'
  outline: '#8d9194'
  outline-variant: '#43474a'
  surface-tint: '#bbc9d1'
  primary: '#bbc9d1'
  on-primary: '#253239'
  primary-container: '#243138'
  on-primary-container: '#8b99a1'
  inverse-primary: '#536068'
  secondary: '#b0c9e9'
  on-secondary: '#18324c'
  secondary-container: '#304863'
  on-secondary-container: '#9fb7d7'
  tertiary: '#9dd75b'
  on-tertiary: '#1e3700'
  tertiary-container: '#1e3600'
  on-tertiary-container: '#70a62f'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d6e5ee'
  primary-fixed-dim: '#bbc9d1'
  on-primary-fixed: '#101d24'
  on-primary-fixed-variant: '#3b4950'
  secondary-fixed: '#d1e4ff'
  secondary-fixed-dim: '#b0c9e9'
  on-secondary-fixed: '#001d35'
  on-secondary-fixed-variant: '#304863'
  tertiary-fixed: '#b8f473'
  tertiary-fixed-dim: '#9dd75b'
  on-tertiary-fixed: '#0f2000'
  on-tertiary-fixed-variant: '#2e4f00'
  background: '#121414'
  on-background: '#e2e2e2'
  surface-variant: '#333535'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Hanken Grotesk
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.04em
  headline-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-padding: 32px
  gutter: 24px
  section-gap: 48px
  card-inner-padding: 24px
---

## Brand & Style

The design system is built for the "Nocturnal Scholar"—a persona that thrives in quiet, focused, late-night environments where high-level academic research meets cutting-edge technology. The brand personality is **Futuristic-Academic**: sophisticated, intellectual, and slightly avant-garde, yet deeply human-centric and "cozy."

The visual style is a fusion of **Glassmorphism** and **Modern Corporate**. It leverages the depth and translucency of glass to suggest the layering of complex information, while maintaining the structural rigor of a premium analytics dashboard. The aesthetic should evoke a sense of calm focus through deep, dark backgrounds and soft, glowing elements that guide the user's eye toward AI-driven insights.

## Colors

The palette is optimized for low-light environments to reduce eye strain during extended study sessions.

- **Primary Background:** A deep navy-charcoal (#243138) provides a solid, infinite base.
- **Secondary Surfaces:** Soft blue-grey (#4A627E) is used for secondary UI elements and navigation containers.
- **AI Accent:** An olive-to-yellow-green range (#7AB139) is reserved exclusively for AI features, "Ask AI" buttons, and critical data highlights, creating a distinct visual "glow" against the dark base.
- **Content:** Neutral light grey (#EAEAEA) ensures high legibility for body text and primary data labels.
- **Gradients:** Use purple-to-navy glassmorphic gradients for sidebar overlays or background decorative orbs to add depth and a "premium" feel.

## Typography

This design system utilizes **Hanken Grotesk** exclusively to maintain a sleek, geometric, yet legible aesthetic.

- **Headlines:** Use tighter letter spacing and heavier weights to command attention.
- **Body Text:** Use `body-md` for standard editorial content. Ensure a generous line height (minimum 1.5x font size) to maintain the "cozy academic" feel.
- **AI Interactions:** When the AI is "speaking," use `body-lg` with a slightly increased font weight (500) to distinguish it from static research content.

## Layout & Spacing

The layout follows a **Fluid Grid** model with a focus on wide gutters and generous margins to prevent information density from feeling overwhelming.

- **Desktop:** 12-column grid, 24px gutters, 32px side margins.
- **Tablet:** 8-column grid, 16px gutters, 24px side margins.
- **Mobile:** 4-column grid, 16px gutters, 16px side margins.

Information is grouped into logical "clusters" or "pods." Use the `section-gap` of 48px to clearly separate different analytical modules, ensuring the UI breathes and maintains its premium editorial character.

## Elevation & Depth

Visual hierarchy is established through **Tonal Layering** and **Glassmorphism**:

1.  **Level 0 (Base):** Primary background (#243138).
2.  **Level 1 (Containers):** Semi-transparent glass cards with a subtle 1px border (`rgba(255, 255, 255, 0.1)`) and a backdrop blur of 12px-20px.
3.  **Level 2 (Popovers/Active Elements):** Elevated glass surfaces with a soft, diffused shadow (Color: `#000000`, Blur: 30px, Opacity: 40%) and a purple-tinted ambient glow.

Avoid harsh drop shadows. Depth should feel like physical glass layers resting on a dark velvet surface.

## Shapes

The design system uses a **Generous Rounded** language to soften the "futuristic" technicality with a "human-centric" touch.

- **Cards/Containers:** Large 24px radius (`rounded-xl` and above) to create a soft, approachable frame for complex data.
- **Action Buttons:** Fully pill-shaped (100px) to maximize touch/click comfort and differentiate from content containers.
- **Inputs:** A more structured 12px radius to maintain a sense of precision.

## Components

### Buttons
- **Primary:** Pill-shaped, AI-accent gradient text on a dark glass background, or solid olive (#7AB139) for high-importance actions.
- **Secondary:** Transparent with a 1px light grey border and pill-shaped.

### Cards
- Always feature a 24px corner radius.
- Backgrounds use the `glass_surface` variable with a 16px-24px backdrop blur.
- Use internal padding of 24px to ensure content does not feel cramped against the rounded corners.

### "Ask AI" Input
- A floating, glassmorphic bar anchored to the bottom of the screen.
- Features a subtle animated glow using the AI accent color when active.
- Uses the `display-md` typography for high-visibility prompts.

### Data Visualization
- Charts should use the secondary blue-grey for axes and neutral light grey for labels.
- Data lines or bars should utilize the AI accent (#7AB139) to represent insights or predicted values.

### Chips/Tags
- Small, pill-shaped elements with a subtle purple-to-navy background for categorizing research papers or topics.