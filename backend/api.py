import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # ADD THIS
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import from main.py
from main import OUTPUT_COLUMNS, prepare_data_for_place

app = FastAPI(title="Bike Stress Network API")

# ADD CORS MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # Allows all origins - for production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)


class NetworkRequest(BaseModel):
    city: str

    class Config:
        json_schema_extra = {"example": {"city": "Somerville, Massachusetts, USA"}}


@app.get("/")
def read_root():
    """Root endpoint with API information."""
    return {
        "message": "Bike Stress Network API",
        "endpoints": {
            "/getNetwork": "POST - Get bike network GeoJSON for a place",
            "/docs": "Interactive API documentation",
        },
    }


@app.post("/getNetwork")
def get_network_geojson(request: NetworkRequest):
    """
    Get the bike network GeoJSON for a place.

    Example request body:
    {
        "city": "Somerville, Massachusetts, USA"
    }
    """
    try:
        # Process the data
        nodes, edges = prepare_data_for_place(request.city)

        # Filter down to output columns
        edges = edges[OUTPUT_COLUMNS]

        # Add "_python" suffix to all computed score columns
        score_columns = [
            "lanes_int_score",
            "maxspeed_int_score",
            "separation_level_score",
            "street_classification_score",
            "composite_score",
        ]
        for col in score_columns:
            edges.rename(columns={col: f"{col}_python"}, inplace=True)

        # Convert to GeoJSON
        geojson_str = edges.to_json()
        geojson_dict = json.loads(geojson_str)

        return JSONResponse(content=geojson_dict)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing city '{request.city}': {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
