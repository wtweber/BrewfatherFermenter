from modules import cbpi
from thread import start_new_thread
import logging
import requests
import datetime
import json

drop_first = None
debug = True

brewfather_fermenter_comment = None
brewfather_custom_stream = None

def log(s, d=False):
    if debug or d:
        cbpi.app.logger.info(s)
        return True
    else:
        return False

@cbpi.initalizer()
def init(cbpi):
    log("Brefather Fermenter plugin Initialize", True)

    global brewfather_fermenter_comment
    global brewfather_custom_stream

    brewfather_fermenter_comment = cbpi.get_config_parameter("brewfather_fermenter_comment", None)
    brewfather_custom_stream = cbpi.get_config_parameter("brewfather_custom_stream", None)

    if brewfather_fermenter_comment is None:
        try:
            cbpi.add_config_parameter("brewfather_fermenter_comment", "", "text", "Brefather Fermenter Comment")
        except:
            cbpi.notify("Brefather Error", "Unable to update Brefather comment parameter", type="danger")

    if brewfather_custom_stream is None:
        try:
            cbpi.add_config_parameter("brewfather_custom_stream", "", "text", "Brefather custom data string")
        except:
            cbpi.notify("Brefather Error", "Unable to update Brefather custom data string", type="danger")
    pass

@cbpi.backgroundtask(key="brewfather_fermenter_task", interval=900)
def brewfather_fermenter_background_task(api):

    IFTTTurl = "https://maker.ifttt.com/trigger/fermenter/with/key/oIpkDiy95gLSnzaJ6NvHv"
    global drop_first

    if drop_first is None:
        log("Initial boot skipping first log to prevent over logging")
        drop_first = False
        return False

    if brewfather_custom_stream is None:
        return False

    now = datetime.datetime.now()

    BrewfatherURL = "http://log.brewfather.net/stream"
    headers = {
        'Content-Type': 'application/json',
        'Cache-Control': "no-cache"
    }
    querystring = {'id':cbpi.get_config_parameter("brewfather_custom_stream", None)}

    unit = cbpi.get_config_parameter("unit", "")
    comment = cbpi.get_config_parameter("brewfather_fermenter_comment", "")

    for key, fermenter in cbpi.cache.get("fermenter").iteritems():
        payload = {}
        payload.update({'name':fermenter.name})
        payload.update({'temp_unit':unit})
        payload.update({'comment':comment})

        payload.update({'temp':cbpi.cache.get("sensors").get(fermenter.sensor).instance.last_value})

        #payload.update({'value2':fermenter.sensor3})
        # for key2, sensor in cbpi.cache.get("sensors").iteritems():
        #     if str(fermenter.sensor) == str(sensor.instance.id):
        #         payload.update({'temp':sensor.instance.last_value})
        #     elif str(fermenter.sensor2) == str(sensor.instance.id):
        #         payload.update({'aux_temp':sensor.instance.last_value})
        #     elif str(fermenter.sensor3) == str(sensor.instance.id):
        #         payload.update({'ext_temp':sensor.instance.last_value})
                #payload.update({'value2':sensor.instance.last_value})
        #payload.update({'value2':cbpi.cache.get("sensors").get(value.sensor).instance.last_value})
        brewfatherRequest = requests.request("POST", BrewfatherURL, data=json.dumps(payload), headers=headers, params=querystring)
        if brewfatherRequest:
            log("Brewfather logging %s. Data sent:%s"%(brewfatherRequest.json()['result'],json.dumps(payload)))
        else:
            cbpi.notify("Brefather Error", "Error logging to Brewfather.", type="danger")
            log("Brewfather logging Error! URL:%s Body:%s"%(brewfatherRequest.request.url, brewfatherRequest.request.body),True)
        if debug:
            r = requests.request("POST", IFTTTurl, data = {'value1':json.dumps(payload),'value2':brewfatherRequest.status_code,'value3':brewfatherRequest.text})
    pass
