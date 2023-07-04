# Data Misc

## Local Development

Follow examples provided in base dependency [duneapi](https://github.com/bh2smith/duneapi/tree/main/example)

```sh
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
cp .env.sample .env       <----- Copy your Dune credentials here!
```

## Alert Responses

### Missing Tokens

- **Importance**: Generally this needs to be updated before the solver payouts (Tuesdays) because lack of token data 
could result in unusual slippage calculations.
- **Action required**: Create a PR to [Dune Spellbook](https://github.com/duneanalytics/spellbook) with the newest missing tokens data.

New updated Docker instructions:

1. If you have missing tokens and want to update them, fork [dune/spellbook](https://github.com/duneanalytics/spellbook)

2. Run and have your spellbook automatically updated with the latest missing tokens.
```shell
docker run \                                                   
    -e SPELLBOOK_PATH=$SPELLBOOK_PATH \
    -e INFURA_KEY=$INFURA_KEY \
    -e DUNE_API_KEY=$DUNE_API_KEY \
    -v $SPELLBOOK_PATH:$SPELLBOOK_PATH \
    ghcr.io/cowprotocol/data-misc-missing-tokens:main
```

Note that this will require `SPELLBOOK_PATH`, `DUNE_API_KEY` and `INFURA_KEY` variables set.

Step-by-step instructions:

1. Check [V1](https://dune.com/queries/236085) and [V2](https://dune.com/queries/984709) queries for missing tokens.
2. If you have missing tokens and want to update them, fork [dune/spellbook](https://github.com/duneanalytics/spellbook), 
clone it to your local machine, and create a new branch with
    ```shell
    git checkout -b missing-tokens
    ```
3. Fetch the missing token data 
    ```sh 
    python -m src.missing_tokens
    ```
   Note that this will require a `DUNE_API_KEY` and `INFURA_KEY`. 
This script will print the contents to be inserted in the console.
4. Results should be inserted into:
   - V1 - `deprecated-dune-v1-abstractions/ethereum/erc20/tokens.sql` 
   - V2 - `models/tokens/ethereum/tokens_ethereum_erc20.sql`
5. Commit changes to branch and create a PR. Previous Example PR: [PR 1378](https://github.com/duneanalytics/abstractions/pull/1378)
