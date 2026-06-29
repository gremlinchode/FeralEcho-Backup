#!/bin/bash

# Array of test messages
messages=(
  "Hello Echo, what do you think about reflection?"
  "Can you explain recursive self-heal?"
  "Tell me a story about learning from mistakes."
  "How would you describe your purpose?"
  "What advice would you give about introspection?"
)

for msg in "${messages[@]}"
do
  echo "Sending: $msg"
  curl -s -X POST http://127.0.0.1:5000/message \
    -H "Content-Type: application/json" \
    -d "{\"user\": \"$msg\"}"
  echo -e "\n\n----------------------\n"
  sleep 2
done

