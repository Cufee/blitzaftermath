from pymongo import MongoClient

from datetime import datetime, timedelta


class BansAPI():
    def __init__(self):
        client = MongoClient("mongodb://51.222.13.110:27017")
        self.bans_collection = client.webapp.bans

    def ban_user(self, discord_user_id, reason, notified, min, hrs=0, days=0):
        '''Bans a user by id for "days" of days and with "reason" as reason'''
        ban_data = {
            'user_id': discord_user_id,
            'expiration': (datetime.utcnow() + timedelta(minutes=min) + timedelta(hours=hrs) + timedelta(days=days)),
            'timestamp': datetime.utcnow(),
            'notified': notified,
            'reason': reason,
            'notified': True
        }

        self.bans_collection.insert_one(ban_data)
        return None