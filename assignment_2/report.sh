

run_combination() {
  # $1 is the maximum delay
  # #2 is the Packet Discard Probability

  sh network.sh $1 $2 & 
  files = "small.txt medium.txt large.txt"
  results=()
  for f in $files
  do
    run_attempt f
    results+=($?)
  done 
  echo results

}

run_attempt() {
  # $1 is the filename for the size.
  
  filename = $1
  sh testing.sh $1
  sh testing.sh $1
  sh testing.sh $1
  value=$(<time.log)
  
}
