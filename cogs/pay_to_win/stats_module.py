from discord import Embed

from cloudinary import config
from cloudinary.api import delete_resources, resources
from cloudinary.uploader import upload

import requests
import rapidjson

class CustomBackground():
    def __init__(self):
        self.updateBGAPI = "http://158.69.62.236/setnewbg/"
        self.deleteBGAPI = "http://158.69.62.236/removebg/"


    def put(self, user_id: str, image_url: str) -> (str):
        """Upload a new image or update the existing one"""
        url = self.updateBGAPI + user_id + "?bgurl=" + image_url
        res = requests.get(url)
        try:
            res_data = rapidjson.loads(res.text)
        except:
            print(url, res, res.text)
            raise Exception("It looks like Aftermath fancy is currently down for maintenance.")
        
        if res_data.get("error"):
            return res_data.get("error")
        else:
            return None
        

    def delete(self, user_id: str) -> str:
        url = self.deleteBGAPI + user_id
        res = requests.get(url)
        res_data = {}
        try:
            res_data = rapidjson.loads(res.text)
        except:
            print(url, res, res.text)
            raise Exception("It looks like Aftermath fancy is currently down for maintenance.")

        if res_data and res_data.get("error", None):
            return res_data.get("error")
        else:
            return None
