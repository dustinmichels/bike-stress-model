# !/bin/zsh

# copy somerville
cp backend/data/out/main/somerville_streets.geojson frontend/public/somerville_streets.geojson

# copy cambridge
cp backend/data/out/main/cambridge_streets.geojson frontend/public/cambridge_streets.geojson

# copy everett
cp backend/data/out/main/everett_streets.geojson frontend/public/everett_streets.geojson

# copy charts, if any
cp backend/data/out/notebook/chart*.html deployed-charts


