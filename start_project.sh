
SESSION="maison-core"
PROJECT_DIR=~/Maison-core
VENV_PATH="$PROJECT_DIR/venv/bin/activate"

#check if session exists
tmux has-session -t $SESSION 2>/dev/null

if [ $? != 0 ]; then 
    tmux set-option -g mouse on
    tmux new-session -d -s $SESSION -n "postgres_container"
    tmux send-keys -t $SESSION:postgres "sleep 10 && docker exec -it postgres_db psql -U postgres -d maison" C-m

   

    tmux set-option -g mouse on
    tmux new-window -t $SESSION -n 'docker'
    tmux send-keys -t $SESSION:docker "cd $PROJECT_DIR/docker" C-m
    tmux send-keys -t $SESSION:docker "source $VENV_PATH" C-m
    tmux send-keys -t $SESSION:docker "docker-compose up --build" C-m


    tmux set-option -g mouse on
    tmux new-window -t $SESSION -n 'docker_alembic'
    tmux send-keys -t $SESSION:docker_alembic "cd $PROJECT_DIR" C-m
    tmux send-keys -t $SESSION:docker_alembic "source $VENV_PATH" C-m
    tmux send-keys -t $SESSION:docker_alembic "sleep 10 && docker exec  -it maison /bin/bash" C-m

    tmux set-option -g mouse on
    tmux new-window -t $SESSION -n 'npm_servers'
    tmux send-keys -t $SESSION:npm_servers "cd $PROJECT_DIR/frontend/app" C-m
    tmux send-keys -t $SESSION:npm_servers "source $VENV_PATH" C-m
    tmux send-keys -t $SESSION:npm_servers "sleep 10 && npm run dev"

    
    
    # tmux set-option -g mouse on
    # tmux new-window -t $SESSION -n 'docker'
    # tmux send-keys -t $SESSION:docker "cd $PROJECT_DIR" C-m
    # tmux send-keys -t $SESSION:docker "docker-compose up --build" C-m
fi


###start up for tmux(command):
# """" 
# --tmux ls
# -- tmux kill-session -t task-manager-fastapi(kill existing sessions)
# -- chmod +x ~/task-manager-fastapi/app/start_project.sh
# --  ./app/start_project.sh
# --  tmux attach-session -t task-manager-fastapi

# """"

# windows 2
#     tmux new-window -t $SESSION -n 'celery'
#     tmux send-keys -t $SESSION:celery  "cd $PROJECT_DIR" C-m
#     tmux send-keys -t $SESSION:celery "source $VENV_PATH" C-m
#     tmux send-keys -t $SESSION:celery "celery -A app.core.celery_worker.celery_app worker --loglevel=info" C-m

 # #pane 2
    # tmux set-option -g mouse on
    # tmux split-window -h -t $SESSION
    # tmux send-keys -t $SESSION "cd $PROJECT_DIR" C-m
    # tmux send-keys -t $SESSION "source $VENV_PATH" C-m
    # tmux send-keys -t $SESSION "celery -A app.core.celery_worker.celery_app worker --loglevel=info" C-m