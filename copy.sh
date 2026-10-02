#!/bin/zsh

# copy somerville
cp backend/data/out/main/somerville_streets.geojson frontend/public/somerville_streets.geojson

# copy cambridge
cp backend/data/out/main/cambridge_streets.geojson frontend/public/cambridge_streets.geojson

# copy everett
cp backend/data/out/main/everett_streets.geojson frontend/public/everett_streets.geojson

# copy malden
cp backend/data/out/main/malden_streets.geojson frontend/public/malden_streets.geojson

# copy charts, if any
for f in backend/data/out/notebook/chart*.html(N); do
  cp "$f" deployed-charts
done
