
# Source _env/bin/activate if it exists
if [ -f "_env/bin/activate" ]; then
    source _env/bin/activate
fi
# Export PYTHONPATH to include the current directory
export PYTHONPATH=$(pwd):$PYTHONPATH
# Print the PYTHONPATH for verification
echo "PYTHONPATH set to: $PYTHONPATH"
