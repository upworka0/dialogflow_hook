from flask import Flask, request, make_response, jsonify
import os
import requests

app = Flask(__name__)

count = 0

@app.route('/')
def index():
    return 'Hello World!'

# function for responses
def results():
    global count
    # build a request object
    req = request.get_json(force=True)
    # fetch action from json
    action = req.get('queryResult').get('action')
    print(req)
    # return a fulfillment response
    count = count + 1
    return {'fulfillmentText': 'This is a Question %s' % count}


# create a route for webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    return make_response(jsonify(results()))


# run the app
if __name__ == '__main__':
    app.run()
