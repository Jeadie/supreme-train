run_peers() {
  port=$(cat port.txt) 
  rm Shared/second.txt
  echo "This is the first file that needs to be made." > Shared/first.txt
  sh peer.sh 127.0.0.1 $port 15 &  run_second_peer $port
}

run_second_peer() {
    mkdir peer_2 
    sleep 2
    cp -r ./*  peer_2/
    cd peer_2/
    echo "This is a second file for the second peer." > Shared/second.txt
    cp README.md Shared/
    sh peer.sh 127.0.0.1 $1 1
    cd -
    rm -r peer_2/
}

sh tracker.sh & sleep 5 && run_peers
