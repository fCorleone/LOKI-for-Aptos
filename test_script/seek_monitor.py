import argparse
import json
import re
import os
import time
from datetime import datetime


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

    return parser.parse_args()


def parse_timestamp(line):
    timestamp_pattern = r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)"
    match = re.search(timestamp_pattern, line)
    if match:
        return datetime.strptime(match.group(1), "%Y-%m-%dT%H:%M:%S.%fZ")
    return None


def find_first_timestamp(log_file_path):
    with open(log_file_path, 'r') as log_file:
        for line in log_file:
            timestamp = parse_timestamp(line)
            if timestamp:
                return timestamp
    return None


def main():
    args = parse_arguments()

    with open(args.input, 'r') as f:
        config = json.load(f)

    loki_node_id = int(config.get("loki_id"))
    cluster_path = config.get("cluster_mint").rsplit('/', 1)[0]

    log_file_path = f"{cluster_path}/{loki_node_id}/log"

    if not os.path.exists(log_file_path):
        print(f"Log file does not exist: {log_file_path}")
        return

    print("*********")
    print(f"Monitoring log file: {log_file_path}")
    print("*********\n")
    print("@@ Start Monitor LOKI node MUTATE! @@\n")

    # Initialize the monitor dictionary
    monitor_dict = {
        "mutate_vote": 0,
        "mutate_timestamp": 0,
        "mutate_round": 0,
        "mutate_payload": 0
    }

    # Precompile keyword regular expressions
    keywords = list(monitor_dict.keys())
    keyword_patterns = {key: re.compile(key, re.IGNORECASE) for key in keywords}

    # Find the first timestamp record from the log and use it as the start time for monitoring
    start_timestamp = find_first_timestamp(log_file_path)
    if not start_timestamp:
        print("No valid timestamp found in the log file.")
        return

    print(f"Monitoring started. First timestamp in log: {start_timestamp}")

    file_offset = 0
    end_timestamp = None

    try:
        while True:
            with open(log_file_path, 'r') as log_file:
                log_file.seek(file_offset)

                # reading new content
                new_lines = log_file.readlines()

                # update the file offset
                file_offset = log_file.tell()

            for line in new_lines:
                line = line.strip()
                if not line:
                    continue
                print(line)

                timestamp = parse_timestamp(line)

                for key in keywords:
                    if monitor_dict[key] == 0 and keyword_patterns[key].search(line):
                        monitor_dict[key] = 1
                        print(f"Detected '{key}', updated monitor_dict: {monitor_dict}")

                        end_timestamp = timestamp

                # Determine if all keywords have been detected
                if all(value == 1 for value in monitor_dict.values()):
                    duration = (end_timestamp - start_timestamp).total_seconds()
                    print("\n*********")
                    print("All keywords detected.")
                    print(f"Start time: {start_timestamp}")
                    print(f"End time: {end_timestamp}")
                    print(f"Time taken: {duration:.2f} seconds")
                    print("*********\n")
                    return

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
