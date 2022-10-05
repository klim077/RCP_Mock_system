#!/bin/sh

echo "$0 start"

echo "$0 end"

# Hand off to the CMD
echo "$0 handing off to $@"
exec "$@"
