WITH
traded_tokens as (
    SELECT * from (
        SELECT
            distinct("sellToken") as token,
            count(*) as ct
        FROM gnosis_protocol_v2."GPv2Settlement_evt_Trade"
        WHERE evt_block_time > now() - interval '3 Month'
        GROUP BY token
        UNION ALL
        SELECT
            distinct("buyToken") as token,
            count(*) as ct
        FROM gnosis_protocol_v2."GPv2Settlement_evt_Trade"
        WHERE evt_block_time > now() - interval '3 Month'
        GROUP BY token
    ) buy_sell_tokens
),

token_counter as (
    SELECT
        token,
        sum(ct) as popularity
    FROM traded_tokens
    WHERE token != '\xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
    GROUP BY token
    ORDER BY popularity desc
),

traded_tokens_without_prices as (
    SELECT
        symbol,
        CONCAT('0x', ENCODE(contract_address, 'hex')) as address,
        popularity,
        decimals
    FROM token_counter
    INNER JOIN erc20.tokens
        ON contract_address = token
    WHERE token NOT IN (select distinct(contract_address) from prices.usd)
    ORDER BY popularity DESC, symbol
)

select * from traded_tokens_without_prices