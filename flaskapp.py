from flask import Flask, request, make_response, jsonify
import os
app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello World!'

def save_file(text):
    with open("static/log.txt", 'a') as f:
        f.write(text)


# function for responses
def results():
    # build a request object
    req = request.get_json(force=True)

    # fetch action from json
    action = req.get('queryResult').get('action')
    save_file(action)
    # return a fulfillment response
    return {'fulfillmentText': 'This is a response from webhook.'}


# create a route for webhook
@app.route('/webhook')
def webhook():
    return make_response(jsonify(results()))


# run the app
if __name__ == '__main__':
   app.run()
