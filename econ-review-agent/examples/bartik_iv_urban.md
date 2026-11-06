# Immigration and Housing Rents in US Metropolitan Areas: A Shift-Share Approach

*(Synthetic example written for testing this review agent — not a real paper.)*

## Abstract

We study the effect of immigrant inflows on housing rents across US
metropolitan areas between 1990 and 2015. Because immigrants select
destinations partly in response to local economic conditions, OLS estimates of
the rent effect are biased. We instrument actual immigrant inflows with a
shift-share (Bartik) instrument that interacts 1980 settlement patterns of
immigrants by country of origin with subsequent national inflows from each
origin country. A 1 percentage point increase in the immigrant share of an
MSA's population raises average rents by 2.1 percent and house prices by 3.4
percent. Effects are larger in MSAs with inelastic housing supply, consistent
with a standard spatial equilibrium model.

## Research Design

### Data

The sample is a panel of 219 MSAs observed in 1990, 2000, 2007, and 2015.
Immigrant populations by country of origin and MSA come from the decennial
Census and the American Community Survey. Median rents and house values come
from the same sources, deflated to 2015 dollars. Housing supply elasticities
are taken from Saiz (2010).

### Empirical Strategy

We estimate:

    d ln(R_mt) = beta * d (ImmigrantShare_mt) + X_mt * gamma + tau_t + u_mt

in long differences across census periods, where R_mt is the median rent in
MSA m at time t. The immigrant share is instrumented with the shift-share
instrument:

    Z_mt = sum_o ( share_mo,1980 * NationalInflow_ot )

where share_mo,1980 is the fraction of origin-o immigrants living in MSA m in
1980 and NationalInflow_ot is the national inflow from origin o in period t.
The exclusion restriction requires that 1980 settlement patterns are unrelated
to unobserved determinants of rent growth decades later, conditional on
controls. We control for census-division-by-period fixed effects, the 1980
industry mix, and initial skill composition. Standard errors are clustered by
MSA. First-stage F statistics exceed 40 in all specifications.
