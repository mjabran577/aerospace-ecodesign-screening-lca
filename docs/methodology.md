# Methodology

## Goal

Demonstrate a transparent, reproducible Ecodesign workflow for a generic aluminium aerospace/avionics enclosure.

## Functional unit

One generic aluminium equipment enclosure.

## Scope

This is a **screening LCA / Ecodesign portfolio model**, focused primarily on a climate-change indicator.

Included:
- aluminium material production
- manufacturing electricity
- inbound road freight
- end-of-life recovery as a mass-flow/circularity indicator
- scenario comparison
- hotspot analysis
- sensitivity analysis
- factor provenance and system-boundary metadata

Excluded:
- detailed alloying elements
- machining consumables/coolants
- surface treatments
- electronics
- launch/mission operations
- toxicity/resource/water impact categories
- avoided-burden credits at end of life

## Calculation principle

For each activity:

`activity data × controlled impact factor = impact contribution`

The model intentionally keeps factors outside the code in `data/emission_factors.csv`.

## Important boundary caveat

The public factors used here do **not all have identical system boundaries**.

For example:
- primary aluminium is cradle-to-gate,
- recycled aluminium is gate-to-gate,
- German electricity is a direct CO2 factor rather than a full life-cycle CO2e factor,
- road freight is an operational screening proxy.

Because of that, the output is labelled a **screening result**, not a comparative assertion or ISO-conformant LCA result.

A real study should harmonize boundaries and use a consistent LCI/LCIA database such as the company's licensed LCA database / ESA-compatible datasets.
