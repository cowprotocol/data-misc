# Data Misc

## Local Development

Follow examples provided in base dependency [duneapi](https://github.com/bh2smith/duneapi/tree/main/example)

```sh
python3 -m venv venv
source ./env/bin/activate
pip install -r requirements.txt
cp .env.sample .env       <----- Copy your Dune credentials here!
```

## Alert Responses

### Missing Tokens

- **Importance**: Generally this needs to be updated before the solver payouts (Tuesdays) because lack of token data 
could result in unusual slippage calculations.
- **Action required**: Create a PR to `dune/abstractions` with the newest missing tokens data.

Instructions:

1. Check [V1](https://dune.com/queries/236085) and [V2](https://dune.com/queries/984709) queries for missing tokens.
2. If you have missing tokens and want to update them, fork [dune/abstractions](https://github.com/duneanalytics/abstractions), 
clone it to your local machine, and create a new branch with `git checkout -b missing-tokens`.
3. If tokens are missing in V1, run: `python -m src.missing_tokens` and append output to `ethereum/erc20/tokens.sql`
4. If tokens are missing in V2, download output from [V2](https://dune.com/queries/984709) query 
(need to be logged in as `gnosis.protocol`, see: [1password](https://start.1password.com/open/i?a=6DWD777JFFEZZLYS6J4DUURYLE&h=my.1password.com&i=pbtrpawolbhkbpojk6yz7j2kwu&v=weisopuq6vd4jkgfi443z2fe64)) 
run: `python -m src.missing_tokens --token-file downloaded.csv` and append output to `spellbook/models/tokens/ethereum/tokens_ethereum_erc20.sql`
5. Commit changes to branch and create a PR. Previous Example PR: [PR 1378](https://github.com/duneanalytics/abstractions/pull/1378)
