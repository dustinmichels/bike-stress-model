# Bike stress map

The version of the code associated with my advanced GIS class, which won best in show in 2026, see [adv-gis](https://github.com/dustinmichels/bike-stress-model/tree/adv-gis).

## API

```sh
curl -X POST "http://localhost:8000/getNetwork" \
  -H "Content-Type: application/json" \
  -d '{"city": "Somerville, Massachusetts, USA"}'
```

Deployed to render:

```sh
curl -X POST "https://bike-stress-model.onrender.com/getNetwork" \
  -H "Content-Type: application/json" \
  -d '{"city": "Somerville, Massachusetts, USA"}'
```
