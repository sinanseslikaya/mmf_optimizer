#!/bin/bash

# Set the parameters
federal_tax_rate=22
state=VA
state_tax_rate=5.75
investment_amount=10000
bank_apy=4.35

# Initialize variables
total_time=0

# Run the optimizer.py script 100 times
for ((i=1; i<=100; i++))
do
    # run the script and capture the real-time output
    execution_time=$( { time -p python3.11 optimizer.py --federal_tax_rate $federal_tax_rate --state $state --state_tax_rate $state_tax_rate --investment_amount $investment_amount --bank_apy $bank_apy; } 2>&1 | grep real | awk '{print $2}' )

    # echo "Run $i:"
    # echo "Execution time: ${execution_time} seconds"
    # echo

    total_time=$(echo "$total_time + $execution_time" | bc -l)
done

#  average execution time
average_time=$(echo "$total_time / 10" | bc -l)
echo "Average execution time: $average_time seconds"
