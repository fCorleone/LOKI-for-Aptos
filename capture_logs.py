import argparse
import re
import subprocess
import json
import os


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run aptos-forge-cli with specific configurations.", add_help=False)
    parser.add_argument(
        "-v", "--validators", type=int, default=4,
        help="Set the number of all validators (include LOKI, default: 4)"
    )
    parser.add_argument(
        "-l", "--loki_node", type=int, default=1,
        help="Set the number of LOKI nodes (default: 1)"
    )
    parser.add_argument(
        "--log_dir", type=str, default="/root/autodl-tmp/temp_log",
        help=f"Set the log directory path (default: \"/root/autodl-tmp/temp_log\")"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="temp_output_swarm.json",
        help=f"Set the output file path (default: \"temp_output_swarm.json\")"
    )
    parser.add_argument(
        "-h", "--help", action="help", default=argparse.SUPPRESS,
        help="show this help message and exit"
    )

    return parser.parse_args()

def setup_environment_and_clear_logs(tmpdir):
    """Set temporary directory environment variables and clean up old logs"""
    os.environ["TMPDIR"] = tmpdir
    tmp_files = os.path.join(tmpdir, ".tmp*")
    print(f"Cleaning temporary files in: {tmp_files}")
    os.system(f"rm -rf {tmp_files}")

def setup_environment(tmpdir):
    """Set the temporary directory environment variable"""
    os.environ["TMPDIR"] = tmpdir


def extract_and_save_output(output, output_file):
    """Key information is extracted from the child process output and saved as a JSON file"""
    result_data = {
        "loki_url": None,
        "origin_node_url": [],
        "cluster_mint": None
    }

    previous_line = ""
    for line in output.splitlines():
        cluster_dir_pattern = r'Building genesis with \d+ validators\. Directory of output: "(.+)"'
        rest_api_pattern = r'Node \d+: REST API is listening at: (http://127\.0\.0\.1:\d+)'

        cluster_dir_match = re.search(cluster_dir_pattern, line)
        if cluster_dir_match:
            result_data["cluster_mint"] = cluster_dir_match.group(1) + "/root_key"

        rest_api_match = re.search(rest_api_pattern, line)
        if rest_api_match:
            rest_api_url = rest_api_match.group(1)
            # Check that the previous line contains node type information
            if "LOKI-for-Aptos/target/debug/aptos-node\"" in previous_line:
                result_data["loki_url"] = rest_api_url
            elif "LOKI-for-Aptos/target/debug/aptos-node-origin\"" in previous_line:
                result_data["origin_node_url"].append(rest_api_url)

        previous_line = line

    with open(output_file, 'w') as out_file:
        json.dump(result_data, out_file, indent=4)
    print(f"Extracting Successfully, save in: {output_file}")

def run_command(validators, loki_node, output_file_path):
    """Runs the original `cargo run` build and processes the output of the child process"""
    command = [
        "cargo", "run", "-p", "aptos-forge-cli", "--",
        "--suite", "run_forever",
        "--num-validators", str(validators),
        "--num-loki-validator", str(loki_node),
        "test", "local-swarm"
    ]

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        output = ""

        # The output is read and stored in real time
        for line in process.stdout:
            print(line, end="")  # show in terminal
            output += line

            # Detects the program completion flag
            if "The network has been deployed. Hit Ctrl+C to kill this, otherwise it will run forever." in line:
                print("\n@@@ Detected the completion of network deployment, start to extract log information... @@@")
                extract_and_save_output(output, output_file_path)
                break

        process.wait()

    except KeyboardInterrupt:
        print("\nUser interrupt detected, program exit...")
    except Exception as e:
        print(f"Error: {e}")

def main():
    args = parse_arguments()
    print(f"Parameters in running:\nValidators={args.validators}, Loki Node={args.loki_node}, Log Dir={args.log_dir}, Output={args.output}")

    setup_environment(args.log_dir)
    # setup_environment_and_clear_logs(args.log_dir)

    run_command(args.validators, args.loki_node, args.output)

if __name__ == "__main__":
    main()
