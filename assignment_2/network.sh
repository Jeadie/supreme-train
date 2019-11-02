emulator_receive_sender_port=10000
receiver_address=127.0.0.1
receiver_receive_port=10001
emulator_receive_receiver_port=10003
sender_address=127.0.0.1
sender_receive_port=10002
max_delay=${1:-1}
p_discard=${2:-0}
verbose=1

echo "For Sender\n--------------------------------"
echo "  Receive acks from port: ${sender_receive_port}"
echo "  Send data to port:      ${emulator_receive_sender_port}\n"

echo "For Receiver\n--------------------------------"
echo "  Receive data from port: ${receiver_receive_port}"
echo "  Send acks to port:      ${emulator_receive_receiver_port}\n"

echo "Config\n"
echo "  Maximum Delay: ${max_delay}"
echo "  Prob. Discard: ${p_discard}\n"

./nEmulator-linux386 $emulator_receive_sender_port $receiver_address $receiver_receive_port $emulator_receive_receiver_port $sender_address $sender_receive_port $max_delay $p_discard $verbose 
