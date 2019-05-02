#! /bin/sh

if [ -d "/app/media/hhnb/bsp_data_repository" ]
then
    cd "/app/media/hhnb/bsp_data_repository"
elif [ -d "/apps/media/hhnb/bsp_data_repository" ]
then
    cd "/apps/media/hhnb/bsp_data_repository"
fi

UPSTREAM=${1:-'@{u}'}
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse "$UPSTREAM")
BASE=$(git merge-base @ "$UPSTREAM")

if [ ! $LOCAL = $REMOTE ]
then
    date
    git pull
    python create_singlecellmodeling_structure_v2.py optimizations/ singlecellmodeling_structure.json
fi
