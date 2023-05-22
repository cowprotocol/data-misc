from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent

PUBLIC_RESOLVER_ABI = [
    {
        "constant": True,
        "inputs": [
            {"internalType": "bytes32", "name": "node", "type": "bytes32"},
            {"internalType": "string", "name": "key", "type": "string"},
        ],
        "name": "text",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
]
