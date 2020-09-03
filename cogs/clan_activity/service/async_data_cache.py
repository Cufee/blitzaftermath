import asyncio

class AsyncActivityCache():
    """Manage clan activity data cache"""
    def __init__(self):
        # WG API Application ID
        wg_api_app_id = "add73e99679dd4b7d1ed7218fe0be448"

        # WG Stats API URLs
        self.wg_api_personal_data = '/wotb/account/info/?application_id=%s&account_id=' % wg_api_app_id
        self.wg_api_clan_info = '/wotb/clans/accountinfo/?application_id=%s&extra=clan&account_id=' % wg_api_app_id
        self.wg_api_achievements = '/wotb/account/achievements/?application_id=%s&account_id=' % wg_api_app_id
        self.wg_api_statistics_all = '/wotb/account/info/?application_id=%s&extra=statistics.rating&fields=statistics.rating,statistics.all,updated_at,last_battle_time&account_id=' % wg_api_app_id
        self.wg_api_vehicle_statistics = '/wotb/tanks/stats/?application_id=%s&account_id=' % wg_api_app_id
        self.wg_api_vehicle_achievements = '/wotb/tanks/achievements/?application_id=%s&account_id=' % wg_api_app_id

    