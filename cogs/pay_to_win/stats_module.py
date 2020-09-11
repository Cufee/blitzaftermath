from discord import Embed

from cloudinary import config
from cloudinary.api import delete_resources, resources
from cloudinary.uploader import upload

import requests

class CustomBackground():
    def __init__(self):
        config( 
            cloud_name = "vkodev", 
            api_key = "826743222283223", 
            api_secret = "qidZPaMrwgw5wK5ra0ZE33ns468" 
            )


    def put(self, user_id: str, image_url: str) -> (str, str):
        """Upload a new image or update the existing one"""
        # Check NSFW images
        r = requests.post(
            "https://api.deepai.org/api/nsfw-detector",
            data={
                'image': image_url,
            },
            headers={'api-key': '0b9a5fc7-76fc-47a5-8b62-4772146c4c98'}
            )
        score = (r.json().get('output', {}).get('nsfw_score', -1))

        if r.json().get("err") == "error processing given inputs from request":
            return "This does not look like a valid image, try a different format.", None

        elif score == -1:
            return "My NSFW detector broke, try again later.", None

        elif score > 0.7:
            return "This looks like a NSFW image, I am not able to use it.", None

        response = upload(image_url, public_id=user_id, folder="Aftermath", crop="scale", width=400, format="jpg")
        if not response:
            # Request failed / Bad response
            return "No response from server."
        elif response.get("public_id", None):
            # Upload success
            new_url = response.get('secure_url')
            print(new_url)
            return None, new_url
        else:
            return "Upload failed", None


    def delete(self, user_id: str) -> str:
        # Delete user images by public_id
        response = delete_resources(public_ids=f"Aftermath/{user_id}")
        print(response)
        if not response:
            # Request failed / Bad response
            return "No response from server."

        elif response.get('deleted').get(f"Aftermath/{user_id}", "") == 'deleted':
            # Image was deleted
            return None

        elif response.get('deleted').get(f"Aftermath/{user_id}", "") == 'not_found':
            # Image not found / other errors
            return "You do not have a custom background set."

        else:
            # Image not found / other errors
            return response.get('deleted').get(user_id, "error parsing response")
