
SESSION="maison"
PROJECT_DIR=~/maison
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/maison_frontend/app"

VENV_PATH="$BACKEND_DIR/venv/bin/activate"

#check if session exists
tmux has-session -t $SESSION 2>/dev/null

if [ $? != 0 ]; then 
    tmux set-option -g mouse on
    tmux new-session -d -s $SESSION -n "postgres_container"
    tmux send-keys -t $SESSION:postgres "sleep 20 && docker exec -it postgres_db psql -U postgres -d maison_backend" C-m
    tmux split-window -h -t $SESSION:postgres
    tmux send-keys -t $SESSION:postgres "cd $PROJECT_DIR" C-m
    tmux send-keys -t $SESSION:postgres "source $VENV_PATH" C-m
    tmux send-keys -t $SESSION:postgres "sleep 10 && docker exec  -it maison /bin/bash" C-m

    tmux set-option -g mouse on
    tmux new-window -t $SESSION -n 'docker'
    tmux send-keys -t $SESSION:docker "cd $PROJECT_DIR" C-m
    tmux send-keys -t $SESSION:docker "source $VENV_PATH" C-m
    tmux send-keys -t $SESSION:docker "docker-compose up --build -d && docker logs -f maison" C-m

    tmux set-option -g mouse on
    tmux new-window -t $SESSION -n 'frontend'
    tmux send-keys -t $SESSION:frontend "cd $FRONTEND_DIR" C-m
    tmux send-keys -t $SESSION:frontend "npm run dev" C-m

    tmux set-option -g mouse on
    tmux new-window -t $SESSION -n 'stripe_webhooks'
    tmux send-keys -t $SESSION:stripe_webhooks "cd $PROJECT_DIR" C-m
    tmux send-keys -t $SESSION:stripe_webhooks "source $VENV_PATH" C-m
    tmux send-keys -t $SESSION:stripe_webhooks "stripe listen --api-key \$(grep -m1 '^stripe_secret_key=' $BACKEND_DIR/backend/app/.env | cut -d= -f2) --forward-to localhost:8000/api/v1/webhooks" c-m
    tmux split-window -h -t $SESSION:stripe_webhooks
    tmux send-keys -t $SESSION:stripe_webhooks "cd $PROJECT_DIR" C-m
    tmux send-keys -t $SESSION:stripe_webhooks "source $VENV_PATH" C-m
    tmux send-keys -t $SESSION:stripe_webhooks "stripe listen --api-key \$(grep -m1 '^stripe_secret_key=' $BACKEND_DIR/backend/app/.env | cut -d= -f2) --forward-to localhost:8000/api/v1/webhooks/connect/tenant" c-m

    tmux set-option -g mouse on
    tmux new-window -t $SESSION -n 'editor'
    tmux send-keys -t $SESSION:editor "cd $PROJECT_DIR" C-m
    tmux send-keys -t $SESSION:editor "nvim ." C-m

    tmux set-option -g mouse on
    tmux new-window -t $SESSION -n 'usemaison_servers'
    # tmux send-keys -t $SESSION:stripe_webhook "cd $PROJECT_DIR" C-m
    # tmux send-keys -t $SESSION:stripe_webhook "source $VENV_PATH" C-m
    tmux send-keys -t $SESSION:usemaison_servers "ssh ssh.usemaison.io" c-m 
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
