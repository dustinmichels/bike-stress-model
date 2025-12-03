# Bike stress map

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
