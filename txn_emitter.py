import argparse
import json
import subprocess


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run aptos-transaction-emitter with configurations.", add_help=False)
    parser.add_argument(
        "-i", "--input", type=str, default="temp_output_swarm.json",
        help=f"Input the JSON file (default: \"temp_output_swarm.json\")"
    )
    parser.add_argument(
        "--chain-id", type=int, default=4,
        help="Set the chain id (default: 4)"
    )
    parser.add_argument(
        "-m","--mempool-backlog", type=int, default=6000,
        help="Set the mempool backlog (default: 6000)"
    )
    parser.add_argument(
        "-d","--duration", type=int, default=240,
        help="Set the duration (default: 240)"
    )
    parser.add_argument(
        "-t","--txn-expiration", type=int, default=30,
        help="Set the --txn-expiration-time-secs (default: 30)"
    )
    parser.add_argument(
        "--coordination", type=int, default=5,
        help="Set the --coordination-delay-between-instances (default: 5)"
    )
    parser.add_argument(
        "-n","--num-accounts", type=int, default=1000,
        help="Set the number of accounts (default: 1000)"
    )
    parser.add_argument(
        "-h", "--help", action="help", default=argparse.SUPPRESS,
        help="show this help message and exit"
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    with open(args.input, 'r') as f:
        config = json.load(f)

    # target_urls = " ".join(config.get("origin_node_url", []))
    target_urls = config.get("origin_node_url", [])

    # Can't perform bash cat operations directly in subprocess.
    # If necessary, add "shell = True" in subprocess.run()
    # mint_key = "\"$(cat "+ config.get("cluster_mint") + ")\""

    with open(config.get("cluster_mint"), "r") as file:
        mint_key_content = file.read()

    command = [
        "aptos-transaction-emitter",
        "emit-tx",
        "--targets", *target_urls,
        "--chain-id", str(args.chain_id),
        "--mint-key", mint_key_content,
        "--mempool-backlog", str(args.mempool_backlog),
        "--duration", str(args.duration),
        "--txn-expiration-time-secs", str(args.txn_expiration),
        "--coordination-delay-between-instances", str(args.coordination),
        "--num-accounts", str(args.num_accounts)
    ]

    print("Executing command:", " ".join(command), "\n")
    try:
        subprocess.run(command, check=True)
        print("\n@@ Transaction emitted successfully. @@\n")
    except subprocess.CalledProcessError as e:
        print(f"Error in transaction emitter: {e}")


if __name__ == "__main__":
    main()
