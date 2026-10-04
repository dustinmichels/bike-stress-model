#!/bin/zsh

mkdir -p frontend/public/data

# copy somerville
cp data/out/main/somerville_streets.geojson frontend/public/data/somerville_streets.geojson

# copy cambridge
cp data/out/main/cambridge_streets.geojson frontend/public/data/cambridge_streets.geojson

# copy everett
cp data/out/main/everett_streets.geojson frontend/public/data/everett_streets.geojson

# copy malden
cp data/out/main/malden_streets.geojson frontend/public/data/malden_streets.geojson

# copy charts, if any
for f in data/out/notebook/chart*.html(N); do
  cp "$f" deployed-charts
done
