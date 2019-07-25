#! /bin/sh

if [ -d "/app/media/hhnb/" ]
then
    cd "/app/media/hhnb/"
elif [ -d "/apps/media/hhnb/" ]
then
    cd "/apps/media/hhnb/"
fi

date
. /web/bspg/venvbspg/bin/activate
python /web/bspg/deployment/create_singlecellmodeling_structure.py . 
