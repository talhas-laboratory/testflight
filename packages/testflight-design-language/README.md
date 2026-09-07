# `@testflight/design-language`

This package is the code-consumable projection of Testflight's active design-language revision.
Its canonical semantic contract lives in
`workspaces/testflight-product/experience-design/artifacts/design-language.yaml`.

## Use

Bundled applications import the CSS export:

```css
@import "@testflight/design-language/tokens.css";
```

Dependency-free static applications may serve `tokens.css` as a versioned static asset. They must
not maintain a hand-edited copy; use a build or sync step that preserves the package version.

Use semantic variables such as `--tf-color-canvas`, `--tf-color-text`, and
`--tf-color-status-held`. Raw palette values are implementation details, not application APIs.

Before generating or changing user-facing UI, read `generation-contract.md`. A material token or
interaction change requires a product-decision proposal, affected-surface list, accessibility
evaluation, and authorized promotion.

