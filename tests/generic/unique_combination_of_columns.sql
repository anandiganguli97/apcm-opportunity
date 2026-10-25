{% test unique_combination_of_columns(model, columns) %}
-- Fails when any combination of the given columns appears more than once.
select {{ columns | join(', ') }}, count(*) as n
from {{ model }}
group by {{ columns | join(', ') }}
having count(*) > 1
{% endtest %}
