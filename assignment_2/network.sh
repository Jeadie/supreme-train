emulator_receive_sender_port=10000
receiver_address=0.0.0.0
receiver_receive_port=10001
emulator_receive_receiver_port=10003
sender_address=0.0.0.0
sender_receive_port=10002
max_delay=0
p_discard=0
verbose=1

echo "For Sender\n--------------------------------"
echo "  Receive acks from port: ${sender_receive_port}"
echo "  Send data to port:      ${emulator_receive_sender_port}\n"

echo "For Receiver\n--------------------------------"
echo "  Receive data from port: ${receiver_receive_port}"
echo "  Send acks to port:      ${emulator_receive_receiver_port}\n"

./nEmulator-linux386 $emulator_receive_sender_port $receiver_address $receiver_receive_port $emulator_receive_receiver_port $sender_address $sender_receive_port $max_delay $p_discard $verbose 
