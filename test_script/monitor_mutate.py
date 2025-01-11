import argparse
import json
import subprocess


def parse_arguments():
    parser = argparse.ArgumentParser(description="Monitor the mutation record of LOKI", add_help=False)
    parser.add_argument(
        "-i", "--input", type=str, default="temp_output_swarm.json",
        help=f"Input the JSON file (default: \"temp_output_swarm.json\")"
    )

    parser.add_argument(
        "-h", "--help", action="help", default=argparse.SUPPRESS,
        help="show this help message and exit"
    )

    parser.add_argument(
        "-c", "--command", type=str, default="\*@ LOKI:|@\* LOKI:",
        help=f"Command to grep (default: \"*@ LOKI:|@* LOKI:\")"
    )

    return parser.parse_args()



def main():
    args = parse_arguments()

    with open(args.input, 'r') as f:
        config = json.load(f)

    loki_node_id = int(config.get("loki_id"))
    cluster_path = config.get("cluster_mint").rsplit('/', 1)[0]  # Remove the last "root_key"

    loki_log_path = f"{cluster_path}/{loki_node_id}/log"

    # First, tail the log file
    tail_command = ["tail", "-f", f"{loki_log_path}"]

    # Ensure correct handling of special characters in the command argument
    # This ensures that @ and * are passed literally to grep
    grep_command = ["grep", "-i", f"{args.command}"]

    print("*********\n",
          "Executing command:", " ".join(tail_command),)
    print("Piping to grep command:", " ".join(grep_command),
          "\n*********\n")

    print("@@ Start Monitor LOKI node MUTATE! @@\n")

    try:
        # Use subprocess.Popen to connect tail and grep via pipe
        # This way we use two separate commands in a list, which prevents shell misinterpretation of special characters
        with subprocess.Popen(tail_command, stdout=subprocess.PIPE) as tail_proc:
            with subprocess.Popen(grep_command, stdin=tail_proc.stdout, stdout=subprocess.PIPE) as grep_proc:
                # Wait for the command to complete
                grep_proc.communicate()

        print("\n@@  @@\n")
    except subprocess.CalledProcessError as e:
        print(f"Error in : {e}")


if __name__ == "__main__":
    main()
