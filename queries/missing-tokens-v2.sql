WITH
-- This query can't yet be run via duneapi client,
-- but the results can be fetched from the interface at: https://dune.com/queries/857522
all_tokens as (
    SELECT DISTINCT token FROM (
        SELECT distinct(buyToken) as token
        FROM gnosis_protocol_v2_ethereum.GPv2Settlement_evt_Trade
        UNION
        SELECT distinct(sellToken) as token
        FROM gnosis_protocol_v2_ethereum.GPv2Settlement_evt_Trade
    ) as _
),
missing_tokens as (
    select token
    from all_tokens
    where token not in (select contract_address from tokens_ethereum.erc20)
)

SELECT * FROM missing_tokens