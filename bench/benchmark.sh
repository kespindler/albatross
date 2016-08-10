function run_ab() {
  python3 run_$1.py &
  sleep 1
  PID=$!
  mkdir -p output/$2
  time ab -c 100 -n 5000 http://127.0.0.1:8000/$2 > output/$2/$1.$2.log
  kill $PID
  wait $PID
}

function run_ab_post() {
  python3 run_$1.py &
  sleep 1
  PID=$!
  mkdir -p output/$2
  time ab -c 100 -n 5000 -p data.txt -T application/x-www-form-urlencoded http://127.0.0.1:8000/$2 > output/$2/$1.$2.log
  kill $PID
  wait $PID
}

# run_ab albatross hello
# run_ab tornado hello
# run_ab aiohttp hello

run_ab_post albatross form
run_ab_post tornado form
run_ab_post aiohttp form
