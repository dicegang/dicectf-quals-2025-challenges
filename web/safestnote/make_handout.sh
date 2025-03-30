#!/bin/bash

tar --owner="arx" --group="arx" \
    --transform 's|\.handout$||' \
    $(find challenge -name "*.handout" | sed 's/\.handout$//' | xargs -I{} echo "--exclude={}") \
    -czvf safestnote.tar.gz challenge