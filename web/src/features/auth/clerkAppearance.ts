// Clerk's <SignIn> restyled from the design tokens only: every colour is a `var(--…)` reference.
export const clerkAppearance = {
  variables: {
    colorPrimary: 'var(--primary)',
    colorPrimaryForeground: 'var(--primary-foreground)',
    colorBackground: 'var(--card)',
    colorForeground: 'var(--card-foreground)',
    colorMuted: 'var(--muted)',
    colorMutedForeground: 'var(--muted-foreground)',
    colorNeutral: 'var(--foreground)',
    colorInput: 'var(--card)',
    colorInputForeground: 'var(--card-foreground)',
    colorBorder: 'var(--border)',
    colorRing: 'var(--ring)',
    colorDanger: 'var(--destructive)',
    borderRadius: 'var(--radius)',
    fontFamilyButtons: 'var(--font-display)',
  },
  elements: {
    // The Flat Plate Rule: hairline border, no shadow, card radius.
    cardBox: { boxShadow: 'none', border: '1px solid var(--border)', borderRadius: 'calc(var(--radius) * 1.4)' },
    card: { boxShadow: 'none' },
    // The Outline button: ink stroke at 60%, signage label.
    socialButtonsBlockButton: {
      minHeight: '2.5rem',
      // Clerk draws button borders as a box-shadow ring; keep its focus ring.
      '&:not(:focus-visible)': {
        boxShadow: '0 0 0 1px color-mix(in oklab, var(--card-foreground) 60%, transparent)',
      },
      letterSpacing: '0.06em',
      textTransform: 'uppercase',
    },
    socialButtonsBlockButtonText: { fontSize: '0.875rem', fontWeight: 600, color: 'var(--card-foreground)' },
    // Our screen carries the headline; Clerk's footer holds the sign-up link.
    header: { display: 'none' },
    footer: { display: 'none' },
  },
} as const
