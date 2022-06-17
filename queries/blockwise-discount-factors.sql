with 
sourced_cow_transfers as (
    -- Incoming COW
    select evt_tx_hash,
           evt_block_time,
           evt_block_number,
           "to" as account,
           value as cow_amount,
           0 as vcow_amount
    from cow_protocol."CowProtocolToken_evt_Transfer"
    union all
    -- Outgoing COW
    select evt_tx_hash,
           evt_block_time,
           evt_block_number,
           "from"     as account,
           -1 * value as cow_amount,
           0 as vcow_amount
    from cow_protocol."CowProtocolToken_evt_Transfer"
    union all
    -- Incoming vCOW
    select evt_tx_hash,
           evt_block_time,
           evt_block_number,
           "to" as account,
           0 as cow_amount,
           value as vcow_amount
    from cow_protocol."CowProtocolVirtualToken_evt_Transfer"
    union
    -- Outgoing vCOW
    select evt_tx_hash,
           evt_block_time,
           evt_block_number,
           "from"     as account,
           0 as cow_amount,
           -1 * value as vcow_amount
    from cow_protocol."CowProtocolVirtualToken_evt_Transfer"
),

balances_at_block as (
    select 
        evt_block_time,
        evt_block_number,
        account,
        cow_amount as cow_delta,
        sum(cow_amount) OVER (PARTITION BY account ORDER BY evt_block_number) as cow_balance,
        vcow_amount as vcow_delta,
        sum(vcow_amount) OVER (PARTITION BY account ORDER BY evt_block_number) as vcow_balance
    from sourced_cow_transfers
),

blockwise_combined_balances as (
    select
        evt_block_time,
        evt_block_number,
        account,
        (vcow_balance + cow_balance) / 10 ^18 as combined_balance
    from balances_at_block
    where evt_block_number > 14475154
    and (vcow_balance + cow_balance) > 10^21
    and account != '\x0000000000000000000000000000000000000000'
),
-- Snapshot
-- https://snapshot.org/#/cow.eth/proposal/0x4bb9b614bdc4354856c4d0002ad0845b73b5290e5799013192cbc6491e6eea0e
-- Tier 1 1,000 COW Discount: 5%
-- Tier 2 10,000 COW Discount: 10%
-- Tier 3 100,000 COW Discount: 20%
-- Tier 4 1,000,000 COW Discount: 40%
subsidy_tiers as (
    SELECT * FROM (VALUES
        -- (0, 10^3, 0.0),
        (10^3, 10^4, 0.05),
        (10^4, 10^5, 0.1),
        (10^5, 10^6, 0.2),
        (10^6, 10^12, 0.4) -- use an essentially infinite upper bound for the top tier!
    ) as t (lower_bound, upper_bound, discount)
),

blockwise_discount as (
    select
        evt_block_time,
        evt_block_number,
        account,
        combined_balance,
        (select max(discount) from subsidy_tiers where combined_balance >= lower_bound) as discount
    from blockwise_combined_balances
),

fee_discounts as (
    select
        trader,
        block_time,
        max(evt_block_time) balance_from,
        fee_usd as fee_paid,
        discount
    from gnosis_protocol_v2."trades" t
    join blockwise_discount
        on account = trader
        and evt_block_time < block_time
    -- https://etherscan.io/tx/0x1100cd4a50a2c224ec39f861aef7574df394edb2b5ed850705cf0bb34f6a300d
    where block_time > '2022-03-28 14:19' -- number = 14475154
    group by trader, block_time, fee_usd, discount
),

-- feePaid = fullFee * (1 - discount)
-- => fullFee = feePaid / (1 - discount)
-- => subsidy = fullFee - feePaid
--            = feePaid / (1 - discount) - feePaid
--            = feePaid * (1 / (1- discount) - 1)
--            = feePaid * discount / (1 - discount)
blockwise_total_subsidy as (
    select
        block_time,
        sum(
            case
                when discount is not null then fee_paid * discount / (1 - discount)
                else 0
            end
        ) as subsidy_usd
    from fee_discounts
    group by block_time
)
select
    sum(subsidy_usd / price) as eth_spent,
    100.0 * sum(case when subsidy_usd is null then 1 else 0 end) / count(*) as percent_missing
from blockwise_total_subsidy
join prices.layer1_usd_eth
    on minute > '2022-03-28 14:19'
    and minute = date_trunc('minute', block_time)
