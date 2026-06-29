#!/bin/zsh
cd ~/Desktop/FeralEcho
source ~/miniforge3/etc/profile.d/conda.sh
conda activate feral_echo
export TOKENIZERS_PARALLELISM=false
export ECHO_DONT_KILL_ME_DADDY=1
export FLASK_ENV=development
export OLLAMA_KEEP_ALIVE=30s
export OLLAMA_NUM_PARALLEL=1

WATCHDOG_LOG=~/Desktop/FeralEcho/memory/echo_watchdog.log

while true; do
    # Hunt down and kill anything holding port 5000 before boot
    PID=$(lsof -t -i :5000)
    if [ ! -z "$PID" ]; then
        echo "[WATCHDOG] $(date -u +%Y-%m-%dT%H:%M:%SZ) Port 5000 is blocked by PID $PID. Clearing..." | tee -a "$WATCHDOG_LOG"
        kill -9 $PID 2>/dev/null
        sleep 1
    fi

    echo "[WATCHDOG] $(date -u +%Y-%m-%dT%H:%M:%SZ) Starting Echo (PID will follow)" | tee -a "$WATCHDOG_LOG"
    python -u run.py 2>&1 | tee -a "$WATCHDOG_LOG"
    # $pipestatus[1] captures python's exit code; $? would capture tee's
    echo "[WATCHDOG] $(date -u +%Y-%m-%dT%H:%M:%SZ) Echo exited with code ${pipestatus[1]}. Restarting in 10s..." | tee -a "$WATCHDOG_LOG"
    sleep 10
done
