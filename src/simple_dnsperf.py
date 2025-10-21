import subprocess
import re
import math


def compute_ci(mean: float, std: float, n: int):
    if not mean or not std or not n:
        return
    z = 1.96  # Approx for 95% CI
    se = std / math.sqrt(n)
    lower = mean - z * se
    upper = mean + z * se
    return f"{lower * 1000:.1f} - {upper * 1000:.1f}"


dns_servers = {
    "1.1.1.1": "Cloudflare",
    "1.0.0.1": "Cloudflare",
    "76.76.2.0": "Control D",
    "76.76.10.0": "Control D",
    "103.247.36.36": "DNSFilter",
    "103.247.37.37": "DNSFilter",
    "8.8.8.8": "Google",
    "8.8.4.4": "Google",
    "208.67.222.222": "Umbrella",
    "208.67.220.220": "Umbrella",
    "9.9.9.9": "Quad9",
    "149.112.112.112": "Quad9",
    "64.6.64.6": "UltraDNS",
    "64.6.65.6": "UltraDNS",
    # "95.85.95.85": "Gcore",
    # "2.56.220.2": "Gcore",
    # "195.46.39.39": "SafeDNS",
    # "195.46.39.40": "SafeDNS",
}

domains_file = "domains.txt"  # Your domain list file
duration = 3  # Test duration in seconds
rate = 50  # Limit query rate (QPS)

# Regex patterns to extract metrics
patterns = {
    "qps": r"Queries per second:\s+([0-9.]+)",
    "avg_latency": r"Average Latency \(s\):\s+([0-9.]+)",
    "loss": r"Queries lost:\s+(\d+)",
    "stddev_latency": r"Latency StdDev \(s\):\s+([0-9.]+)",
    "min_latency": r"\(min ([0-9.]+),",
    "max_latency": r", max ([0-9.]+)\)",
    "queries_completed": r"Queries completed:\s+(\d+)",
}

# Print header
print(
    f"{'Server':<17} {'Name':<10} {'QPS':>8} {'Avg(ms)':>7} {'StdDev(ms)':>7}  {'ci_range':>7} {'Min(ms)':>7} {'Max(ms)':>7} {'Lost':>6}"
)
print("-" * 80)


# Extract metrics
def get_val(key):
    m = re.search(patterns[key], output)
    return float(m.group(1)) if m else 0


for server, name in dns_servers.items():
    cmd = [
        "dnsperf",
        "-s",
        server,
        "-d",
        domains_file,
        "-l",
        str(duration),
        "-Q",
        str(rate),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout

    qps = get_val("qps")
    avg = get_val("avg_latency")
    min_lat = get_val("min_latency")
    max_lat = get_val("max_latency")
    stddev = get_val("stddev_latency")
    queries_completed = get_val("queries_completed")
    lost_match = re.search(patterns["loss"], output)
    lost = lost_match and lost_match.group(1)
    # Convert seconds to ms for latency values
    avg_ms = avg and f"{avg * 1000:.1f}"
    min_ms = min_lat and f"{min_lat * 1000:.1f}"
    max_ms = max_lat and f"{max_lat * 1000:.1f}"
    stddev_ms = stddev and f"{stddev * 1000:.1f}"
    ci_range = compute_ci(avg, stddev, 100)
    print(
        f"{server:<17} {name:<10} {qps:>8} {avg_ms:>7} {stddev_ms:>7} {ci_range} {min_ms:>7} {max_ms:>7}  {lost:>6}"
    )
