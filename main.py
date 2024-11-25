from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from immanuel import charts
from immanuel.classes.serialize import ToJSON
import json
import uvicorn

# FastAPI app instance
app = FastAPI()

# Define the input model
class ChartRequest(BaseModel):
    date_time: str  # Birth date and time in ISO format (e.g., "2000-01-01 10:00:00")
    latitude: str   # Latitude in string format (e.g., "32n43" or "32.71667n")
    longitude: str  # Longitude in string format (e.g., "117w09" or "-117.15")
    time_is_dst: bool = False  # Optional flag for daylight saving time
    chart_type: str  # Type of chart to generate (natal, solar_return, progressed, composite, transits)
    partner_date_time: Optional[str] = None  # Needed for composite charts
    partner_latitude: Optional[str] = None  # Needed for composite charts
    partner_longitude: Optional[str] = None  # Needed for composite charts
    target_date: Optional[str] = None  # Needed for solar return or progressed charts (e.g., "2025-06-20 17:00")

@app.post("/generate-chart")
async def generate_chart(chart_request: ChartRequest):
    try:
        # Create the subject using the provided details
        subject = charts.Subject(
            date_time=chart_request.date_time,
            latitude=chart_request.latitude,
            longitude=chart_request.longitude,
            time_is_dst=chart_request.time_is_dst,
        )

        # Get the chart based on chart type
        if chart_request.chart_type == "natal":
            natal_chart = charts.Natal(subject)

        elif chart_request.chart_type == "solar_return":
            if not chart_request.target_date:
                raise HTTPException(status_code=400, detail="Target date is required for Solar Return chart.")
            natal_chart = charts.SolarReturn(subject, int(chart_request.target_date.split('-')[0]))

        elif chart_request.chart_type == "progressed":
            if not chart_request.target_date:
                raise HTTPException(status_code=400, detail="Target date is required for Progressed chart.")
            natal_chart = charts.Progressed(subject, chart_request.target_date)

        elif chart_request.chart_type == "composite":
            if not (chart_request.partner_date_time and chart_request.partner_latitude and chart_request.partner_longitude):
                raise HTTPException(status_code=400, detail="Partner details are required for Composite chart.")
            partner_subject = charts.Subject(
                date_time=chart_request.partner_date_time,
                latitude=chart_request.partner_latitude,
                longitude=chart_request.partner_longitude,
            )
            natal_chart = charts.Composite(subject, partner_subject)

        elif chart_request.chart_type == "transits":
            natal_chart = charts.Transits(latitude=chart_request.latitude, longitude=chart_request.longitude)

        else:
            raise HTTPException(status_code=400, detail="Invalid chart type")

        # Convert the natal chart data to JSON format
        natal_chart_json = json.dumps(natal_chart, cls=ToJSON, indent=4)

        # Return the JSON data
        return {"success": True, "chart": json.loads(natal_chart_json)}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error generating chart: {str(e)}")

# To run locally
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
