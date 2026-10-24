{{ config(materialized='table') }}
select
  b.practice_id, b.practice_name, b.rurality, b.shortage_area, b.svi_percentile,
  p.scenario, p.capture_rate, p.consent_rate,
  count(*) as attributed_beneficiary_months,
  count(*) filter (where b.apcm_code = 'G0556') as g0556_eligible_months,
  count(*) filter (where b.apcm_code = 'G0557') as g0557_eligible_months,
  count(*) filter (where b.apcm_code = 'G0558') as g0558_eligible_months,
  sum(b.monthly_allowed_amount) as full_capture_gross_allowed,
  sum(b.monthly_allowed_amount) * p.capture_rate * p.consent_rate as projected_apcm_allowed,
  sum(b.possible_displaced_allowed_amount) * p.capture_rate * p.consent_rate as possible_displaced_allowed,
  sum(b.monthly_allowed_amount) * p.capture_rate * p.consent_rate
    - sum(b.possible_displaced_allowed_amount) * p.capture_rate * p.consent_rate as modeled_net_change,
  sum(b.modeled_coinsurance) * p.capture_rate * p.consent_rate as modeled_coinsurance_exposure,
  count(*) filter (where b.has_observed_overlap_candidate) as overlap_candidate_months,
  max(b.rate_source_status) as rate_source_status
from {{ ref('int_beneficiary_month_tier') }} b
cross join {{ ref('scenario_assumptions') }} p
where b.monthly_allowed_amount is not null
 group by b.practice_id, b.practice_name, b.rurality, b.shortage_area, b.svi_percentile,
          p.scenario, p.capture_rate, p.consent_rate

