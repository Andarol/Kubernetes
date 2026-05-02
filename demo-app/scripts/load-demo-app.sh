#!/usr/bin/env bash
set -u

BASE_URL="http://192.168.122.100"
HOST_HEADER="demo-app.demo-app"
WORKERS=10
REQUESTS_PER_WORKER=200
CONNECT_TIMEOUT=3
MAX_TIME=8
SLEEP_SECONDS=0

usage() {
  cat <<'EOF'
Usage: ./scripts/load-demo-app.sh [options]

Options:
  --base-url URL              Base URL to hit (default: http://192.168.122.100)
  --host-header HOST          Host header for ingress routing (default: demo-app.demo-app)
                              Use empty value to skip Host header: --host-header ""
  --workers N                 Concurrent workers (default: 10)
  --requests-per-worker N     Requests per worker (default: 200)
  --sleep-seconds N           Delay between requests per worker (default: 0)
  --connect-timeout N         curl connect timeout in seconds (default: 3)
  --max-time N                curl max request time in seconds (default: 8)
  -h, --help                  Show this help

Examples:
  ./scripts/load-demo-app.sh
  ./scripts/load-demo-app.sh --workers 20 --requests-per-worker 300
  ./scripts/load-demo-app.sh --base-url http://192.168.122.100 --host-header demo-app.demo-app
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url)
      BASE_URL="$2"
      shift 2
      ;;
    --host-header)
      HOST_HEADER="$2"
      shift 2
      ;;
    --workers)
      WORKERS="$2"
      shift 2
      ;;
    --requests-per-worker)
      REQUESTS_PER_WORKER="$2"
      shift 2
      ;;
    --sleep-seconds)
      SLEEP_SECONDS="$2"
      shift 2
      ;;
    --connect-timeout)
      CONNECT_TIMEOUT="$2"
      shift 2
      ;;
    --max-time)
      MAX_TIME="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if ! [[ "$WORKERS" =~ ^[0-9]+$ ]] || [[ "$WORKERS" -lt 1 ]]; then
  echo "--workers must be a positive integer" >&2
  exit 1
fi
if ! [[ "$REQUESTS_PER_WORKER" =~ ^[0-9]+$ ]] || [[ "$REQUESTS_PER_WORKER" -lt 1 ]]; then
  echo "--requests-per-worker must be a positive integer" >&2
  exit 1
fi

ENDPOINT="${BASE_URL%/}/api/tasks"
TOTAL_REQUESTS=$((WORKERS * REQUESTS_PER_WORKER))
TMP_DIR="$(mktemp -d)"
START_TS="$(date +%s)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo "Starting load test"
echo "Endpoint: $ENDPOINT"
if [[ -n "$HOST_HEADER" ]]; then
  echo "Host header: $HOST_HEADER"
else
  echo "Host header: <none>"
fi
echo "Workers: $WORKERS"
echo "Requests per worker: $REQUESTS_PER_WORKER"
echo "Total requests: $TOTAL_REQUESTS"
echo ""

run_worker() {
  local worker_id="$1"
  local ok=0
  local fail=0
  local i

  for ((i=1; i<=REQUESTS_PER_WORKER; i++)); do
    local payload http_code
    payload=$(printf '{"title":"load-w%s-r%s-%s"}' "$worker_id" "$i" "$(date +%s%N)")

    if [[ -n "$HOST_HEADER" ]]; then
      http_code=$(curl -sS -o /dev/null -w "%{http_code}" \
        -H "Host: $HOST_HEADER" \
        -H "Content-Type: application/json" \
        --connect-timeout "$CONNECT_TIMEOUT" \
        --max-time "$MAX_TIME" \
        -X POST "$ENDPOINT" \
        -d "$payload" || echo "000")
    else
      http_code=$(curl -sS -o /dev/null -w "%{http_code}" \
        -H "Content-Type: application/json" \
        --connect-timeout "$CONNECT_TIMEOUT" \
        --max-time "$MAX_TIME" \
        -X POST "$ENDPOINT" \
        -d "$payload" || echo "000")
    fi

    if [[ "$http_code" == "201" || "$http_code" == "200" ]]; then
      ok=$((ok + 1))
    else
      fail=$((fail + 1))
    fi

    if [[ "$SLEEP_SECONDS" != "0" ]]; then
      sleep "$SLEEP_SECONDS"
    fi
  done

  echo "$ok $fail" > "$TMP_DIR/worker-${worker_id}.txt"
}

for ((w=1; w<=WORKERS; w++)); do
  run_worker "$w" &
done
wait

TOTAL_OK=0
TOTAL_FAIL=0
for f in "$TMP_DIR"/worker-*.txt; do
  read -r ok fail < "$f"
  TOTAL_OK=$((TOTAL_OK + ok))
  TOTAL_FAIL=$((TOTAL_FAIL + fail))
done

END_TS="$(date +%s)"
DURATION=$((END_TS - START_TS))
if [[ "$DURATION" -le 0 ]]; then
  DURATION=1
fi
RPS=$((TOTAL_OK / DURATION))

echo "Load test complete"
echo "Duration: ${DURATION}s"
echo "Success: $TOTAL_OK"
echo "Failed: $TOTAL_FAIL"
echo "Approx successful RPS: $RPS"

if [[ "$TOTAL_FAIL" -gt 0 ]]; then
  exit 2
fi
