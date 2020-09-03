# Asyncio
import asyncio
import aiohttp
from aiohttp import ClientSession
# MongoDB driver
import motor.motor_asyncio

from time import time
from random import randrange

# Pasted from StackOverflow
async def async_get(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            response = await resp.json()
            status_code = resp.status
    return response, status_code

async def get_wg_api_domain(realm: str = None, player_id: int = None) -> str:
    """Get WG API domain from realm or by player_id length"""
    if not realm and not player_id:
        return "No realm or player_id passed."
    # Detect realm
    id_length = len(str(player_id))
    if realm:
        realm = realm.upper()

    if realm == 'RU' or id_length == 8:
        player_realm = 'RU'
        api_domain = 'http://api.wotblitz.ru'
        status_code = 200

    elif realm == 'EU' or id_length == 9:
        player_realm = 'EU'
        api_domain = 'http://api.wotblitz.eu'
        status_code = 200

    elif realm == 'NA' or id_length == 10:
        player_realm = 'NA'
        api_domain = 'http://api.wotblitz.com'
        status_code = 200

    else:
        api_domain = None
        player_realm = None
        status_code = 404

    return api_domain, player_realm, status_code


class AsyncClanActivityAPI():
    """Async Mongo DB API using Motor"""
    def __init__(self):
        self.counter = 0

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://51.222.13.110:27017", io_loop=self.loop)
        db = client.clan_activity
        self.clans_collection = db.clans
        self.players_collection = db.players
        glossary_db = client.glossary
        self.averages_collection = glossary_db.tankaverages

        # WG API Application ID
        wg_api_app_id = "add73e99679dd4b7d1ed7218fe0be448"

        # WG clans API URLs
        self.wg_api_clan_search = '/wotb/clans/list/?application_id=%s&search=' % wg_api_app_id
        self.wg_api_clan_details = '/wotb/clans/info/?application_id=%s&fields=clan_id,name,tag,is_clan_disbanded,members_ids,updated_at,members&extra=members&clan_id=' % wg_api_app_id

        # # WG accounts API URLs
        # self.wg_api_personal_data = '/wotb/account/info/?application_id=%s&account_id=' % wg_api_app_id
        # self.wg_api_achievements = '/wotb/account/achievements/?application_id=%s&account_id=' % wg_api_app_id
        # self.wg_api_statistics_all = '/wotb/account/info/?application_id=%s&extra=statistics.rating&fields=statistics.rating,statistics.all,updated_at,last_battle_time&account_id=' % wg_api_app_id
        self.wg_api_vehicle_statistics = '/wotb/tanks/stats/?application_id=%s&account_id=' % wg_api_app_id
        # self.wg_api_vehicle_achievements = '/wotb/tanks/achievements/?application_id=%s&account_id=' % wg_api_app_id

    # Clans
    def enable_for_clan(self, *clan_realm_and_tag: tuple):
        start = time()
        coros = []
        for clan_realm, clan_tag in clan_realm_and_tag:
            t = self.async_track_new_clan(clan_realm, clan_tag)
            coros.append(t)
        
        all_groups = asyncio.gather(*coros)
        self.loop.run_until_complete(all_groups)
        delta = time() - start
        print("Updated %s players in %s seconds" % (self.counter, delta))

    async def async_track_new_clan(self, realm: str, clan_tag: str):
        """Enable tracking for a clan by realm and tag"""
        realm_upper = realm.upper()
        clan_tag_upper = clan_tag.upper()
        # Run function for adding a clan
        api_domain, _, status_code = await get_wg_api_domain(realm=realm_upper)
        if status_code != 200:
            print("Unable to get API domain - %s" % status_code)
            return status_code

        # WG Stats API URLs
        clan_search_URL = "".join([api_domain, self.wg_api_clan_search, clan_tag_upper])
        clan_search, status_code =  await async_get(url=clan_search_URL)

        if status_code != 200:
            print("Unable to fetch clan data, server responded with %s" % status_code)
            return status_code
        else:
            clans_raw_list = clan_search.get("data")
            for clan_data in clans_raw_list:
                if clan_data.get("tag") == clan_tag_upper:
                    clan_id = clan_data.get("clan_id", None)
                    break
            # Return 404 if no clan matcher the tag
            if not clan_id:
                print("Clan %s not found on %s" % (clan_tag_upper, realm_upper))
                return 404

            clan_details_URL = "".join([api_domain, self.wg_api_clan_details, str(clan_id)])
            clan_details_res, status_code = await async_get(url=clan_details_URL)
            clan_details = clan_details_res.get("data", {}).get(str(clan_id), {})

            if status_code != 200:
                print("Unable to fetch clan data, server responded with %s" % status_code)
                return status_code
            elif not clan_details:
                print("Failed to fetch clan detailes for %s on %s" % (clan_tag_upper, realm_upper))
                return 404
            else:
                # Add realm to clan data
                clan_details.update({"realm": realm_upper})

            # Update all players in a clan
            players = clan_details.get("members", {})  # Need to add players to DB
            for player_data in players.values():
                player_id = player_data.get("account_id")
                t = self.update_player_in_db(player_data)
                t2 = self.update_player_rating(player_id)
                await self.loop.create_task(t)
                await self.loop.create_task(t2)

            status_code = await self.update_clan_in_db(clan_details)
            return status_code

    async def update_clan_in_db(self, clan_data_input: dict):
        """Update clan entry in db, with upsert"""
        clan_id = clan_data_input.get("clan_id")
        realm = clan_data_input.get("realm")
        clan_name = clan_data_input.get("name")
        clan_tag = clan_data_input.get("tag")
        members_ids = clan_data_input.get("members_ids", [])
        total_rating = clan_data_input.get("total_rating", None)

        new_clan_entry = {
            "_id": clan_id,
            "realm": realm,
            "clan_name": clan_name,
            "clan_tag": clan_tag,
            "members_ids": members_ids,
            "total_rating": total_rating,
        }
        c_filter = {"_id": clan_id}
        result = await self.clans_collection.update_one(c_filter, {"$set": new_clan_entry}, upsert=True)
        # print('Clan updated: %s' % repr(result.raw_result))
        if result.raw_result.get("ok", 0) > 0:
            return 200
        else:
            return 500

    async def get_clan_from_db(self, realm: str, clan_tag: str):
        """Get a clan entry for db"""
        c_filter = {"realm": realm.upper(), "clan_tag": clan_tag.upper()}
        clan_data = await self.clans_collection.find_one(c_filter)
        if not clan_data:
            return 404
        else:
            return 200

    # Players
    async def update_player_in_db(self, player_data_input: dict):
        """Update player entry in db, with upsert"""
        player_id = player_data_input.get("account_id")
        nickname = player_data_input.get("account_name")
        joined_at = player_data_input.get("joined_at")

        new_player_entry = {
            "_id": player_id,
            "nickname": nickname,
            "joined_at": joined_at,
            "premium_expiration": 0,
        }
        exists = await self.players_collection.find_one(new_player_entry)
        if exists:
            return 409
            
        c_filter = {"_id": player_id}
        result = await self.players_collection.update_one(c_filter, {"$set": new_player_entry}, upsert=True)
        # print('Player updated: %s' % repr(result.raw_result))
        if result.raw_result.get("ok", 0) > 0:
            return 200
        else:
            return 500

    async def update_player_rating(self, player_id: int):
        """Update player entry in db, with upsert"""
        p_filter = {"_id": player_id}
        player_data = await self.players_collection.find_one(p_filter)
        if not player_data:
            print("Player %s does not exist in db." % player_id)
            return 404

        api_domain, _, status_code = await get_wg_api_domain(player_id=player_id)
        if status_code != 200:
            print("Unable to get api_domain for %s." % player_id)
            return status_code
        
        detailed_stats_URL = "".join([api_domain, self.wg_api_vehicle_statistics, str(player_id)])
        player_stats_live, status_code = await async_get(detailed_stats_URL)
        if status_code != 200:
            print("Unable to get stats for %s, API responded with %s." % player_id, status_code)
            return status_code
        
        player_vehicles = player_stats_live.get('data', {}).get(str(player_id))
        if not player_vehicles:
            # Request limit reached
            # This is a janky solution, sleep and restart the task
            await asyncio.sleep(1)
            status_code = await self.loop.create_task(self.update_player_rating(player_id))
            return status_code

        # print(player_vehicles)
        battles, raw_rating = 0, 0
        for vehicle in player_vehicles:
            vehicle_data = vehicle.get("all")
            vehicle_data.update({"tank_id": vehicle.get('tank_id')})
            result, status_code = await self.loop.create_task(self.calc_tank_rating(vehicle_data))
            if status_code != 200:
                continue
            r_battles = result.get("battles")
            r_raw_rating = result.get("rating")
            battles += r_battles
            raw_rating += (r_raw_rating * r_battles)

        if battles == player_data.get("battles", 0):
            # Skip if no battles played
            return 409
        elif battles == 0:
            return 404

        average_rating = round(raw_rating / battles)
        new_player_entry = {
            "average_rating": average_rating,
            "battles": battles,
            "rating_updated": 0,
        }
        c_filter = {"_id": player_id}
        result = await self.players_collection.update_one(c_filter, {"$set": new_player_entry}, upsert=True)
        print('Player updated: %s' % repr(result.raw_result))
        if result.raw_result.get("ok", 0) > 0:
            self.counter += 1
            return 200
        else:
            return 500

    async def calc_tank_rating(self, tank_data: dict):
        tank_battles = tank_data.get("battles")
        if tank_battles == 0 or not tank_battles:
            return {"battles": 0, "rating": 0}, 404

        tank_id = int(tank_data.get('tank_id', 0))
        tank_averages = await self.averages_collection.find_one(
            {'tank_id': tank_id})

        if not tank_averages or not tank_averages.get('meanSd'):
            # print(f'Missing data for tank {tank_id}')
            return {"battles": 0, "rating": 0}, 404

        # Expected values
        exp_dmg = tank_averages.get('special', {}).get('damagePerBattle')
        exp_spott = tank_averages.get('special', {}).get('spotsPerBattle')
        exp_frag = tank_averages.get('special', {}).get('killsPerBattle')
        exp_def = (tank_averages.get('all').get(
            'dropped_capture_points') / tank_averages.get('all').get('battles'))
        exp_wr = tank_averages.get('special', {}).get('winrate')
        # Organize data
        tank_avg_wr = (tank_data.get("wins") / tank_battles) * 100
        tank_avg_dmg = tank_data.get(
            'damage_dealt', 0) / tank_battles
        tank_avg_spott = tank_data.get('spotted', 0) / tank_battles
        tank_avg_frag = tank_data.get('frags', 0) / tank_battles
        tank_avg_def = tank_data.get(
            'dropped_capture_points', 0) / tank_battles

        # Calculate WN8 metrics
        rDMG = tank_avg_dmg / exp_dmg
        rSPOTT = tank_avg_spott / exp_spott
        rFRAG = tank_avg_frag / exp_frag
        rDEF = tank_avg_def / exp_def
        rWR = tank_avg_wr / exp_wr

        rWRc = max(0, ((rWR - 0.71) / (1 - 0.71)))
        rDMGc = max(0, ((rDMG - 0.22) / (1 - 0.22)))
        rFRAGc = max(0, (min(rDMGc + 0.2, (rFRAG - 0.12) / (1 - 0.12))))
        rSPOTTc = max(0, (min(rDMGc + 0.1, (rSPOTT - 0.38) / (1 - 0.38))))
        rDEFc = max(0, (min(rDMGc + 0.1, (rDEF - 0.10) / (1 - 0.10))))

        wn8 = round((980*rDMGc) + (210*rDMGc*rFRAGc) + (155*rFRAGc *
                                                        rSPOTTc) + (75 * rDEFc * rFRAGc) + (145 * (min(1.8, rWRc))))

        result = {
            "battles": tank_battles,
            "rating": wn8,
        }

        return result, 200