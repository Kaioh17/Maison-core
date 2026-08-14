# --tmux ls
# -- tmux kill-session -t task-manager-fastapi(kill existing sessions)
# -- chmod +x ~/task-manager-fastapi/app/start_project.sh
# --  ./app/start_project.sh
# --  tmux attach-session -t task-manager-fastapi


# Start Docker Desktop if it isn't already running (WSL2 -> Windows Docker Desktop)
if ! docker info >/dev/null 2>&1; then
  echo "Docker not running — starting Docker Desktop..."
  DOCKER_EXE="/mnt/c/Program Files/Docker/Docker/Docker Desktop.exe"
  if [ -f "$DOCKER_EXE" ]; then
    "$DOCKER_EXE" >/dev/null 2>&1 &
  else
    powershell.exe -Command "Start-Process 'Docker Desktop'" >/dev/null 2>&1
  fi
  # ponytail: fixed 60x2s poll cap, raise if Docker Desktop is slow to boot on this machine
  for i in $(seq 1 60); do
    docker info >/dev/null 2>&1 && break
    sleep 2
  done
  docker info >/dev/null 2>&1 || echo "Warning: Docker still not up after 2 minutes, continuing anyway."
fi

# chmod +x ./start_project.sh
./start_project.sh
tmux a -t maison
