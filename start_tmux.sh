# --tmux ls
# -- tmux kill-session -t task-manager-fastapi(kill existing sessions)
# -- chmod +x ~/task-manager-fastapi/app/start_project.sh
# --  ./app/start_project.sh
# --  tmux attach-session -t task-manager-fastapi


chmod +x ./start_project.sh
./start_project.sh
tmux attach-session -t maison-core
