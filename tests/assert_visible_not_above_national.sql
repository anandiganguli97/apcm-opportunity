-- Visible clinician-level volume should not exceed the national total for a code
-- (small tolerance for rounding of average allowed amounts is not needed: services are counts).
select * from {{ ref('mart_suppression') }}
where visible_services > national_services * 1.001
