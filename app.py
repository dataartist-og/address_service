from flask             import Flask, render_template, jsonify, request, Response
from PIL               import Image, ImageOps
from io                import BytesIO
import joblib
import pickle
import json
import pickle
import numpy as np
import requests
import math
import multiprocessing
import itertools


app = Flask(__name__)

def find_new_latlong(lat1=39.989983,lon1=-86.053014, D=2.5):
  R = 6378.1 #Radius of the Earth
  lat1 = math.radians(lat1) #Current lat point converted to radians
  lon1 = math.radians(lon1) #Current long point converted to radians

  #lat2  52.20444 - the lat result I'm hoping for
  #lon2  0.36056 - the long result I'm hoping for.
  latlng_tuples = []
  for d in np.arange(0.1,D+0.1,0.1):
    for deg_brng in range(1,360,5):
      brng = math.radians(deg_brng)
      lat2 = math.asin( math.sin(lat1)*math.cos(d/R) +
          math.cos(lat1)*math.sin(d/R)*math.cos(brng))

      lon2 = lon1 + math.atan2(math.sin(brng)*math.sin(d/R)*math.cos(lat1),
                  math.cos(d/R)-math.sin(lat1)*math.sin(lat2))

      lat2 = math.degrees(lat2)
      lon2 = math.degrees(lon2)
      latlng_tuples.append((lat2,lon2))
  return latlng_tuples

def reverse_geocode(lat=39.989983,lng=-86.053014):
  latlng = ','.join([str(lat),str(lng)])
  url_parta = "https://maps.googleapis.com/maps/api/geocode/json?latlng="
  url_partb = "&location_type=ROOFTOP&result_type=premise&key=AIzaSyBcAI3cvYnKMxaVLc4ZXpD7iLbtN6YWL3A"
  url = url_parta + latlng + url_partb
  rq = requests.post(url)
  #print (json.loads(rq.content))
  addresses = []
  for jsn in json.loads(rq.content)['results']:
    addresses.append(jsn['formatted_address'])
  return addresses

@app.route('/list_nearby_addresses', methods=['POST'])
def return_address_list():
    """ Make a POST to this endpint and pass in an URL to an image in the body of the request.
        Swap out the model.pkl with another trained model to classify new objects. """

    try:
        body    = request.get_json()
        print(body)
        lat = float(body["lat"])
        lng = float(body["lng"])
        new_tups = find_new_latlong(lat,lng)
        with multiprocessing.Pool(processes=32) as pool:
            results = pool.starmap(reverse_geocode, new_tups)
        returned_addresses = list(itertools.chain.from_iterable(results))
        response = json.dumps({"addresses_nearby": list(set((returned_addresses)))})
        return(response)

    except Exception as e:
        print(e)
        raise

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
