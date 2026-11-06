# The Employment Effects of Minimum Wage Increases: Evidence from Contiguous County Pairs

*(Synthetic example written for testing this review agent — not a real paper.)*

## Abstract

We estimate the effect of minimum wage increases on teen employment using all
state minimum wage changes in the United States between 1994 and 2019. Our
identification strategy compares employment outcomes in contiguous county pairs
that straddle a state border, which allows us to control for local economic
shocks that are common to both counties in a pair. Using quarterly county-level
payroll data, we find that a 10 percent increase in the minimum wage reduces
teen employment by 0.8 percent, an estimate that is substantially smaller than
the consensus from national panel studies. The negative effect is concentrated
in counties with low baseline wage levels. We argue that conventional two-way
fixed effects estimates are biased by spatial heterogeneity in employment
trends that is correlated with the timing of minimum wage legislation.

## Research Design

### Data

We construct a quarterly panel of county-level employment and earnings for
workers aged 16-19 from the Quarterly Workforce Indicators (QWI), 1994Q1 to
2019Q4. Minimum wage data come from state legislative records. We restrict the
sample to the 1,181 county pairs that straddle a state border and have positive
teen employment in every quarter. County-level covariates (population,
industry composition) come from the Census Bureau and County Business Patterns.

### Empirical Strategy

Our baseline specification is a difference-in-differences design estimated on
county pairs:

    ln(E_ipt) = alpha + beta * ln(MW_it) + gamma_i + delta_pt + X_it * theta + e_ipt

where E_ipt is teen employment in county i, pair p, quarter t; MW_it is the
binding minimum wage; gamma_i are county fixed effects; and delta_pt are
pair-by-quarter fixed effects, which absorb any shock common to both counties
in a border pair. Standard errors are clustered at the state level.

The key idea is that counties on opposite sides of a state border share local
labor-market conditions, so the cross-border difference in minimum wages
provides variation that is plausibly unrelated to local demand shocks. Because
states raise minimum wages repeatedly and at different times, treatment is
staggered and continuous. We supplement the baseline with an event-study
specification around large (> 5 percent) minimum wage increases to examine
pre-existing trends.
