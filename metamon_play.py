import argparse
from tqdm import trange
import requests
import os
import sys
import csv
import pandas as pd
from time import sleep
from datetime import datetime


# URLs to make api calls
BASE_URL = "https://metamon-api.radiocaca.com/usm-api"
TOKEN_URL = f"{BASE_URL}/login"
LIST_MONSTER_URL = f"{BASE_URL}/getWalletPropertyBySymbol"
CHANGE_FIGHTER_URL = f"{BASE_URL}/isFightMonster"
START_FIGHT_URL = f"{BASE_URL}/startBattle"
LIST_BATTLER_URL = f"{BASE_URL}/getBattelObjects"
WALLET_PROPERTY_LIST = f"{BASE_URL}/getWalletPropertyList"
LVL_UP_URL = f"{BASE_URL}/updateMonster"
MINT_EGG_URL = f"{BASE_URL}/composeMonsterEgg"
CHECK_BAG_URL = f"{BASE_URL}/checkBag"


def datetime_now():
    return datetime.now().strftime("%m/%d/%Y %H:%M:%S")


def post_formdata(payload, url="", headers=None):
    """Method to send request to game"""
    files = []
    if headers is None:
        headers = {}

    for _ in range(5):
        try:
            # Add delay to avoid error from too many requests per second
            sleep(1.1)
            response = requests.request("POST",
                                        url,
                                        headers=headers,
                                        data=payload,
                                        files=files)
            return response.json()
        except:
            continue
    return {}


def get_battler_score(monster):
    """ Get opponent's power score"""
    return monster["sca"]


def picker_battler(monsters_list):
    """ Picking opponent """
    battlers = list(filter(lambda m: m["rarity"] == "N", monsters_list))

    if len(battlers) == 0:
        battlers = list(filter(lambda m: m["rarity"] == "R", monsters_list))

    battler = battlers[0]
    score_min = get_battler_score(battler)
    for i in range(1, len(battlers)):
        score = get_battler_score(battlers[i])
        if score < score_min:
            battler = battlers[i]
            score_min = score
    return battler


def pick_battle_level(level=1):
    # pick highest league for given level
    if 21 <= level <= 40:
        return 2
    if 41 <= level <= 60:
        return 3
    return 1


class MetamonPlayer:

    def __init__(self,
                 address,
                 sign,
                 msg="LogIn",
                 auto_lvl_up=False,
                 output_stats=False):
        self.no_enough_money = False
        self.output_stats = output_stats
        self.total_bp_num = 0
        self.total_success = 0
        self.total_fail = 0
        self.mtm_stats_df = []
        self.token = None
        self.address = address
        self.sign = sign
        self.msg = msg
        self.auto_lvl_up = auto_lvl_up

    def init_token(self):
        """Obtain token for game session to perform battles and other actions"""
        payload = {"address": self.address, "sign": self.sign, "msg": self.msg,
                   "network": "1", "clientType": "MetaMask"}
        response = post_formdata(payload, TOKEN_URL)
        if response.get("code") != "SUCCESS":
            sys.stderr.write("Login failed, token is not initialized. Terminating\n")
            sys.exit(-1)
        self.token = response.get("data").get("accessToken")

    def change_fighter(self, monster_id):
        """Switch to next metamon if you have few"""
        payload = {
            "metamonId": monster_id,
            "address": self.address,
        }
        post_formdata(payload, CHANGE_FIGHTER_URL)

    def list_battlers(self, monster_id, front=1):
        """Obtain list of opponents"""
        payload = {
            "address": self.address,
            "metamonId": monster_id,
            "front": front,
        }
        headers = {
            "accessToken": self.token,
        }
        response = post_formdata(payload, LIST_BATTLER_URL, headers)
        return response.get("data", {}).get("objects")

    def start_fight(self,
                    my_monster,
                    target_monster_id,
                    loop_count=1):
        """ Main method to initiate battles (as many as monster has energy for)"""
        success = 0
        fail = 0
        total_bp_fragment_num = 0
        mtm_stats = []
        my_monster_id = my_monster.get("id")
        my_monster_token_id = my_monster.get("tokenId")
        my_level = my_monster.get("level")
        my_power = my_monster.get("sca")
        battle_level = pick_battle_level(my_level)

        tbar = trange(loop_count)
        tbar.set_description(f"Fighting with {my_monster_token_id}...")
        for _ in tbar:
            payload = {
                "monsterA": my_monster_id,
                "monsterB": target_monster_id,
                "address": self.address,
                "battleLevel": battle_level,
            }
            headers = {
                "accessToken": self.token,
            }
            response = post_formdata(payload, START_FIGHT_URL, headers)
            code = response.get("code")
            if code == "BATTLE_NOPAY":
                self.no_enough_money = True
                break
            data = response.get("data", {})
            if data is None:
                print(f"Metamon {my_monster_id} cannot fight skipping...")
                break
            fight_result = data.get("challengeResult", False)
            bp_fragment_num = data.get("bpFragmentNum", 10)

            if self.auto_lvl_up:
                # Try to lvl up
                res = post_formdata({"nftId": my_monster_id, "address": self.address},
                                    LVL_UP_URL,
                                    headers)
                code = res.get("code")
                if code == "SUCCESS":
                    tbar.set_description(f"LVL UP successful! Continue fighting with {my_monster_token_id}...")
                    my_level += 1
                    # Update league level if new level is 21 or 41
                    battle_level = pick_battle_level(my_level)

            self.total_bp_num += bp_fragment_num
            total_bp_fragment_num += bp_fragment_num
            if fight_result:
                success += 1
                self.total_success += 1
            else:
                fail += 1
                self.total_fail += 1

        mtm_stats.append({
            "My metamon id": my_monster_token_id,
            "League lvl": battle_level,
            "Total battles": loop_count,
            "My metamon power": my_power,
            "My metamon level": my_level,
            "Victories": success,
            "Defeats": fail,
            "Total egg shards": total_bp_fragment_num,
            "Timestamp": datetime_now()
        })

        mtm_stats_df = pd.DataFrame(mtm_stats)
        print(mtm_stats_df)
        self.mtm_stats_df.append(mtm_stats_df)

    def get_wallet_properties(self):
        """ Obtain list of metamons on the wallet"""
        data = []
        payload = {"address": self.address}
        headers = {
            "accesstoken": self.token,
        }
        response = post_formdata(payload, WALLET_PROPERTY_LIST, headers)
        mtms = response.get("data", {}).get("metamonList", [])
        if len(mtms) > 0:
            data.extend(mtms)
            data = sorted(data, key=lambda metamon: metamon['id'])
        else:
            if 'code' in response and response['code'] == 'FAIL':
                print(response['message'])
        return data

    def list_monsters(self):
        """ Obtain list of metamons on the wallet (deprecated)"""
        payload = {"address": self.address, "page": 1, "pageSize": 60, "payType": -6}
        headers = {"accessToken": self.token}
        response = post_formdata(payload, LIST_MONSTER_URL, headers)
        monsters = response.get("data", {}).get("data", {})
        return monsters

    def battle(self, w_name=None):
        """ Main method to run all battles for the day"""
        if w_name is None:
            w_name = self.address

        summary_file_name = f"{w_name}_summary.tsv"
        mtm_stats_file_name = f"{w_name}_stats.tsv"
        self.init_token()

        wallet_monsters = self.get_wallet_properties()
        print(f"Monsters total: {len(wallet_monsters)}")

        available_monsters = [
            monster for monster in wallet_monsters if monster.get("tear") > 0 and monster.get("level") < 60
        ]
        level60_monsters = [ 
            monster for monster in wallet_monsters if monster.get("level") >= 60
        ]
        stats_l = []
        print(f"Available Monsters : {len(available_monsters)}")
        print(f"Level 60 Monsters : {len(level60_monsters)}")

        for monster in available_monsters:
            monster_id = monster.get("id")
            tear = monster.get("tear")
            level = monster.get("level")
            exp = monster.get("exp")
            if int(level) >= 60 or int(exp) >= 600:
                print(f"Monster {monster_id} cannot fight due to "
                      f"max lvl and/or exp overflow. Skipping...")
                continue
            battlers = self.list_battlers(monster_id)
            battler = picker_battler(battlers)
            target_monster_id = battler.get("id")

            self.change_fighter(monster_id)

            self.start_fight(monster,
                             target_monster_id,
                             loop_count=tear)
            if self.no_enough_money:
                print("Not enough u-RACA")
                break
        total_count = self.total_success + self.total_fail
        success_percent = .0
        if total_count > 0:
            success_percent = (self.total_success / total_count) * 100

        if total_count <= 0:
            print("No battles to record")
            return

        stats_l.append({
            "Victories": self.total_success,
            "Defeats": self.total_fail,
            "Win Rate": f"{success_percent:.2f}%",
            "Total Egg Shards": self.total_bp_num,
            "Datetime": datetime_now()
        })

        stats_df = pd.DataFrame(stats_l)
        print(stats_df)
        if os.path.exists(summary_file_name) and self.output_stats:
            back_fn = f"{summary_file_name}.bak"
            os.rename(summary_file_name, back_fn)
            tmp_df = pd.read_csv(back_fn, sep="\t", dtype="str")
            stats_upd_df = pd.concat([stats_df, tmp_df])
            stats_df = stats_upd_df
            os.remove(back_fn)

        if self.output_stats:
            stats_df.to_csv(summary_file_name, index=False, sep="\t")

        mtm_stats_df = pd.concat(self.mtm_stats_df)
        if os.path.exists(mtm_stats_file_name) and self.output_stats:
            back_fn = f"{mtm_stats_file_name}.bak"
            os.rename(mtm_stats_file_name, back_fn)
            tmp_df = pd.read_csv(back_fn, sep="\t", dtype="str")
            upd_df = pd.concat([mtm_stats_df, tmp_df])
            mtm_stats_df = upd_df
            os.remove(back_fn)
        if self.output_stats:
            mtm_stats_df.to_csv(mtm_stats_file_name, sep="\t", index=False)

    def mint_eggs(self):
        self.init_token()

        headers = {
            "accessToken": self.token,
        }
        payload = {"address": self.address}

        # Check current egg fragments
        check_bag_res = post_formdata(payload, CHECK_BAG_URL, headers)
        items = check_bag_res.get("data", {}).get("item")
        total_egg_fragments = 0

        for item in items:
            if item.get("bpType") == 1:
                total_egg_fragments = item.get("bpNum")
                break

        total_egg = int(int(total_egg_fragments) / 1000)

        if total_egg < 1:
            print("You don't have enough egg fragments to mint")
            return

        # Mint egg
        res = post_formdata(payload, MINT_EGG_URL, headers)
        code = res.get("code")
        if code != "SUCCESS":
            print("Mint eggs failed!")
            return

        print(f"Minted Eggs Total: {total_egg}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input-tsv", help="Path to tsv file with wallets' "
                                                  "access records (name, address, sign, login message) "
                                                  "name is used for filename with table of results. "
                                                  "Results for each wallet are saved in separate files",
                        default="wallets.tsv", type=str)
    parser.add_argument("-nl", "--no-lvlup", help="Disable automatic lvl up "
                                                  "(if not enough potions/diamonds it will be disabled anyway) "
                                                  "by default lvl up will be attempted after each battle",
                        action="store_true", default=False)
    parser.add_argument("-nb", "--skip-battles", help="No battles, use when need to only mint eggs from shards",
                        action="store_true", default=False)
    parser.add_argument("-e", "--mint-eggs", help="Automatically mint eggs after all battles done for a day",
                        action="store_true", default=False)
    parser.add_argument("-s", "--save-results", help="To enable saving results on disk use this option. "
                                                     "Two files <name>_summary.tsv and <name>_stats.tsv will "
                                                     "be saved in current dir.",
                        action="store_true", default=False)

    args = parser.parse_args()

    if not os.path.exists(args.input_tsv):
        print(f"Input file {args.input_tsv} does not exist")
        sys.exit(-1)

    # determine delimiter char from given input file
    with open(args.input_tsv) as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.readline(), "\t ;,")
        delim = dialect.delimiter

    wallets = pd.read_csv(args.input_tsv, sep=delim)

    auto_lvlup = not args.no_lvlup
    for i, r in wallets.iterrows():
        mtm = MetamonPlayer(address=r.address,
                            sign=r.sign,
                            msg=r.msg,
                            auto_lvl_up=auto_lvlup,
                            output_stats=args.save_results)

        if not args.skip_battles:
            mtm.battle(w_name=r["name"])
        if args.mint_eggs:
            mtm.mint_eggs()
