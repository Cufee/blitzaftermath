from discord import Embed

from cloudinary.api import delete_resources, resources
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url


class CustomBackground():
    def get(self, user_id: str) -> str:
        # Get image from public_id
        image_res = resources(public_id=user_id, max_results=1)
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
        response = upload(image_url, public_id=user_id)
        print(response)
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
        print(response)
        if not response:
            # Request failed / Bad response
            return "No response from server."

        elif response.get('deleted').get(user_id, "") == 'deleted':
            # Image was deleted
            return None

        else:
            # Image not found / other errors
            return response.get('deleted').get(user_id, "error parsing response")
