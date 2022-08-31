SELECT 
    num_trades,
    CONCAT('0x', ENCODE(tx_hash, 'hex')) as txHash 
FROM gnosis_protocol_v2."batches" b
where block_time > now() - interval '5 hour'
ORDER BY block_time DESC;
