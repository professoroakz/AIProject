#!/bin/bash

#create backup on remote machine
ssh root@107.170.228.84 'cd /tmp && mongodump -o movieratings_stream'

#copy to local machine in backup directory
scp -r root@107.170.228.84:/tmp/movieratings_stream ~/movieratings_stream

#rename file to contain current date and time
mv ~/movieratings_stream ~/movieratings_stream.`date "+%Y-%m-%d-%H%M"`

cd ~/movieratings_stream

# Local:
mongorestore movieratings_stream/tweets.bson