WITH 
all_tokens as (
  SELECT DISTINCT token
  FROM (
      SELECT distinct("buyToken") as token
      FROM gnosis_protocol_v2."GPv2Settlement_evt_Trade"
      union
      SELECT distinct("sellToken") as token
      FROM gnosis_protocol_v2."GPv2Settlement_evt_Trade"
    ) as _
),
missing_tokens as (
  select token
  from all_tokens
  where token not in (
      select contract_address
      from erc20.tokens
    )
)
SELECT *
FROM missing_tokens