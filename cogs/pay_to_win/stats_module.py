from discord import Embed

from cloudinary.api import delete_resources, resources
from cloudinary.uploader import upload

import requests

class CustomBackground():
    def get(self, user_id: str) -> str:
        # Get image from public_id
        image_res = resources(public_id=user_id)
        if not image_res:
            # Request failed / Bad response
            return "No response from server."
        else:
            # Search through res to get the image
            image_url = None
            for r in image_res.get('resources', []):
                if r.get('public_id') == user_id:
                    image_url = r.get('url')
                    break
            return image_url


    def put(self, user_id: str, image_url: str) -> str:
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
        if score == -1:
            return "My NSFW detector broke, try again later."
        if score > 0.7:
            return "This looks like a NSFW image, I am not able to use it."

        response = upload(image_url, public_id=user_id)
        if not response:
            # Request failed / Bad response
            return "No response from server."
        elif response.get("public_id", None):
            # Upload success
            return None
        else:
            return "Upload failed"


    def delete(self, user_id: str) -> str:
        # Delete user images by public_id
        response = delete_resources(public_ids=user_id)
        if not response:
            # Request failed / Bad response
            return "No response from server."

        elif response.get('deleted').get(user_id, "") == 'deleted':
            # Image was deleted
            return None

        else:
            # Image not found / other errors
            return response.get('deleted').get(user_id, "error parsing response")
