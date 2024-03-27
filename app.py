# Import the dependencies.
from flask import Flask, jsonify
import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt


#################################################
# Database Setup
# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with = engine)
# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station
# Create our session (link) from Python to the DB
engine = create_engine("sqlite://Resources/hawaii.sqlite")


#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################
# Flask Setup
app = Flask(__name__)

def get_year_ago_date():
    """Helper function to get the date one year ago from the last record."""
    session = Session(engine)
    latest_date = session.query(func.max(measurement.date)).scalar()
    session.close()
    return dt.datetime.strptime(latest_date, "%Y-%m-%d") - dt.timedelta(days=365)

def valid_date(datestr):
    """Helper function to check if a date string is valid."""
    try:
        dt.datetime.strptime(datestr, "%Y-%m-%d")
        return True
    except ValueError:
        return False

# Flask Routes
@app.route("/")
def homepage():
    """List all available API routes."""
    return """
    <html>
        <head>
            <title>Hawaii Climate Analysis API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #dae8fc; }
                h1 { color: #333366; }
                p { color: #333366; font-weight: bold;}
                ul { list-style-type: none; padding: 0; }
                li { margin: 10px 0; }
                a { color: color: #333366; text-decoration: none; }
                a:hover { color: #0077cc; text-decoration: underline; }
                label { color: #333366; font-weight: bold; }
                button {
                    background-color: #333366; 
                    color: white; 
                    border: none;
                    padding: 10px 15px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 16px;
                    margin: 4px 2px;
                    cursor: pointer;
                    border-radius: 5px; 
                }
            </style>
            <script>
                function redirectToStartRoute() {
                    var startDate = document.getElementById('start-date').value;
                    if (startDate) {
                        window.location.href = '/api/v1.0/' + startDate;
                    } else {
                        alert('Please enter a start date.');
                    }
                }

                function redirectToStartEndRoute() {
                    var startDate = document.getElementById('start-end-date').value;
                    var endDate = document.getElementById('end-date').value;
                    if (startDate && endDate) {
                        window.location.href = '/api/v1.0/' + startDate + '/' + endDate;
                    } else {
                        alert('Please enter both start and end dates.');
                    }
                }
            </script>
        </head>
        <body>
            <h1>Welcome to the Hawaii Climate Analysis API</h1>
            <p>Available Routes:</p>
            <ul>
                <li><a href="/api/v1.0/precipitation">Precipitation Data for One Year</a></li>
                <li><a href="/api/v1.0/stations">List of Active Weather Stations</a></li>
                <li><a href="/api/v1.0/tobs">Temperature Observations of the Most-Active Station for One Year</a></li>
                <li>
                    <label for="start-date">Select a date to get temperature data:</label>
                    <input type="date" id="start-date" min="2010-01-01" max="2017-08-23">
                    <button onclick="redirectToStartRoute()">Get Start Date Data</button>
                </li>
                <li>
                    <label for="start-end-date">Select a date range to get temperature data: Start Date:</label>
                    <input type="date" id="start-end-date" min="2010-01-01" max="2017-08-23">
                    <label for="end-date">End Date:</label>
                    <input type="date" id="end-date" min="2010-01-01" max="2017-08-23">
                    <button onclick="redirectToStartEndRoute()">Get Start-End Date Data</button>
                </li>
            </ul>
        </body>
    </html>
    """

@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    year_ago_date = get_year_ago_date()
    results = session.query(measurement.date, measurement.prcp).filter(measurement.date >= year_ago_date).all()
    session.close()

    if not results:
        return jsonify({"error": "No precipitation data found."})

    # Format the results as a dictionary
    precipitation_data = {date: prcp for date, prcp in results}

    return jsonify(precipitation_data)

@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    # Query to retrieve all station data
    stations_results = session.query(Station.name, Station.station, Station.elevation, Station.latitude, Station.longitude).all()
    session.close()

    if not stations_results:
        return jsonify({"error": "No station data found."})

    # Format the results as a list of dictionaries
    stations_data = [{"name": name, "station": station, "elevation": elevation, "latitude": latitude, "longitude": longitude} for name, station, elevation, latitude, longitude in stations_results]

    return jsonify(stations_data)

@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    year_ago_date = get_year_ago_date()

    # Query to retrieve temperature observations for the most active station for the last year
    tobs_results = session.query(measurement.date, measurement.tobs).filter(measurement.station == 'USC00519281').filter(measurement.date >= year_ago_date).all()
    session.close()

    if not tobs_results:
        return jsonify({"error": "No temperature observation data found."})

    # Format the results as a list of dictionaries
    tobs_data = [{"date": date, "temperature": tobs} for date, tobs in tobs_results]

    return jsonify(tobs_data)



@app.route("/api/v1.0/<start>")
def start(start):
    session = Session(engine)

    # Using the helper function for date validation
    if not valid_date(start):
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."})

    # Query to retrieve temperature statistics from the given start date
    temp_results = session.query(func.min(measurement.tobs), func.max(measurement.tobs), func.avg(measurement.tobs)).filter(measurement.date >= start).all()
    session.close()

    if not temp_results or temp_results[0][0] is None:
        return jsonify({"error": "No temperature data found for the given start date."})

    min_temp, max_temp, avg_temp = temp_results[0]

    # Format the results as a dictionary
    temp_data = {
        "Start Date": start,
        "Minimum Temperature": min_temp,
        "Maximum Temperature": max_temp,
        "Average Temperature": avg_temp
    }

    return jsonify(temp_data)


@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):
    session = Session(engine)

    # Using the helper function for both start and end date validation
    if not valid_date(start) or not valid_date(end):
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."})

    # Query to retrieve temperature statistics for the given date range
    temp_results = session.query(func.min(measurement.tobs), func.max(measurement.tobs), func.avg(measurement.tobs)).filter(measurement.date >= start, measurement.date <= end).all()
    session.close()

    if not temp_results or temp_results[0][0] is None:
        return jsonify({"error": "No temperature data found for the given date range."})

    min_temp, max_temp, avg_temp = temp_results[0]

    # Format the results as a dictionary
    temp_data = {
        "Start Date": start,
        "End Date": end,
        "Minimum Temperature": min_temp,
        "Maximum Temperature": max_temp,
        "Average Temperature": avg_temp
    }

    return jsonify(temp_data)


if __name__ == '__main__':
    app.run(debug=True)


