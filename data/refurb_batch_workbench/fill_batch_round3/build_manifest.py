import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ROUND_DIR = Path(__file__).resolve().parent
LEDGER = ROOT / "data/refurb_batch_workbench/ledger.json"
METADATA = ROUND_DIR / "page_metadata.json"


def rel(path):
    return os.path.relpath(ROOT / path, ROUND_DIR)


ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
rows = {row["row_number"]: row for row in ledger["batches"][0]["rows"]}


def make_task(row_number, product_name, output_name, parent_sku, variation_theme,
              price, material, color="", size="", set_count=1, variants=None,
              extra_fields=None, parent_extra_fields=None, base_title=None):
    row = rows[row_number]
    source_links = row.get("source_links") or [{"url": row.get("link", "")}]
    task = {
        "name": row["product_name"],
        "product_name": product_name,
        "template": rel(row["source_template"]),
        "competitors": [f"reference/row{row_number}_{index}.html" for index, _ in enumerate(source_links, 1)],
        "output_name": output_name,
        "logistics_tier": "le_4_oz",
        "store_id": "1店",
        "parent_sku": parent_sku,
        "variation_theme": variation_theme,
        "material": material,
        "set_count": set_count,
    }
    if row_number == 124:
        task["online_price"] = price
    else:
        task["estimated_price"] = price
    if color:
        task["color"] = color
    if size:
        task["size"] = size
    if variants:
        task["variants"] = variants
    if extra_fields:
        task["extra_fields"] = extra_fields
    if parent_extra_fields:
        task["parent_extra_fields"] = parent_extra_fields
    if base_title:
        task["base_title"] = base_title
    return task


tasks = [
    make_task(22, "Butterfly Underwear", "内裤蝴蝶S码M码V1", "TTCA-ButterflyUnderwear", "SIZE", 2.99,
              "Polyamide and Spandex", color="Multicolor", set_count=3,
              variants=[
                  {"sku": "TTCA-ButterflyUnderwear-S", "size": "S", "set_count": 3},
                  {"sku": "TTCA-ButterflyUnderwear-M", "size": "M", "set_count": 3},
              ]),
    make_task(23, "Cotton Underwear", "内裤棉M码5件装V1", "TTCA-CottonUnderwear", "SIZE/NUMBER_OF_ITEMS", 2.99,
              "Cotton", color="Multicolor", size="M", set_count=5,
              variants=[{"sku": "TTCA-CottonUnderwear-M-5pcs", "size": "M", "set_count": 5}]),
    make_task(37, "Camo Mask", "面罩迷彩全脸款V1", "TTCA-CamoMask", "COLOR", 3.49,
              "Polyester", set_count=3,
              variants=[
                  {"sku": "TTCA-CamoMask-GreenCamo", "color": "Green Camo", "set_count": 3},
                  {"sku": "TTCA-CamoMask-BlueCamo", "color": "Blue Camo", "set_count": 3},
              ]),
    make_task(38, "Neck Gaiter", "面罩围脖款V1", "TTCA-NeckGaiter", "COLOR", 3.49,
              "Polyester", set_count=3,
              variants=[
                  {"sku": "TTCA-NeckGaiter-DarkSet", "color": "Dark Set", "set_count": 3},
                  {"sku": "TTCA-NeckGaiter-LightSet", "color": "Light Set", "set_count": 3},
              ]),
    make_task(41, "Toilet Cover", "马桶垫V1", "TTCA-ToiletCover", "NUMBER_OF_ITEMS", 1.99,
              "Polyester", color="Multicolor", set_count=1,
              variants=[{"sku": "TTCA-ToiletCover-1pc", "set_count": 1}]),
    make_task(42, "Ankle Socks", "袜子5双装V1", "TTCA-AnkleSocks", "NUMBER_OF_ITEMS", 2.99,
              "Cotton Blend", color="Multicolor", set_count=5,
              variants=[{"sku": "TTCA-AnkleSocks-5pairs", "set_count": 5}]),
    make_task(44, "Cooling Sleeve", "冰袖冰川款V1", "TTCA-CoolingSleeve", "COLOR", 1.99,
              "Polyester", color="Glacier", set_count=2,
              variants=[{"sku": "TTCA-CoolingSleeve-Glacier", "color": "Glacier", "set_count": 2}],
              base_title="Cooling Arm Sleeves for Men and Women, Ice Silk Sports Arm Covers for Cycling, Running and Outdoor Activities"),
    make_task(47, "Bento Box", "保鲜盒2件装V1", "TTCA-BentoBox", "NUMBER_OF_ITEMS", 2.49,
              "Plastic", color="Clear", set_count=2,
              variants=[{"sku": "TTCA-BentoBox-2pcs", "set_count": 2}]),
    make_task(48, "Cleaning Brush", "清洁果蔬4件装V1", "TTCA-CleaningBrush", "NUMBER_OF_ITEMS", 1.99,
              "Plastic", color="Multicolor", set_count=4,
              variants=[{"sku": "TTCA-CleaningBrush-4pcs", "set_count": 4}]),
    make_task(49, "Ice Tray", "冰块托盘V1", "TTCA-IceTray", "NUMBER_OF_ITEMS", 2.99,
              "Silicone", color="Multicolor", set_count=1,
              variants=[{"sku": "TTCA-IceTray-1pc", "set_count": 1}]),
    make_task(50, "Gradient Sleeve", "冰袖渐变色V1", "TTCA-GradientSleeve", "COLOR", 2.99,
              "Polyester", set_count=2,
              variants=[
                  {"sku": "TTCA-GradientSleeve-PinkYellow", "color": "Pink Yellow", "set_count": 2},
                  {"sku": "TTCA-GradientSleeve-BluePink", "color": "Blue Pink", "set_count": 2},
                  {"sku": "TTCA-GradientSleeve-BlueYellow", "color": "Blue Yellow", "set_count": 2},
              ],
              base_title="2 Pairs Gradient Cooling Arm Sleeves, Ice Silk Sports Arm Covers for Cycling, Running and Outdoor Activities"),
    make_task(53, "Tweezer Set", "镊子4件套V1", "TTCA-TweezerSet", "NUMBER_OF_ITEMS", 2.99,
              "Stainless Steel", color="Silver", set_count=4,
              variants=[{"sku": "TTCA-TweezerSet-4pcs", "set_count": 4}]),
    make_task(71, "Sewing Kit", "针线包27件套V1", "TTCA-SewingKit", "NUMBER_OF_ITEMS", 2.99,
              "Metal and Polyester", color="Multicolor", set_count=27,
              variants=[{"sku": "TTCA-SewingKit-27pcs", "set_count": 27}]),
    make_task(72, "Cycling Shorts", "骑行短裤M码2XL码V1", "TTCA-CyclingShorts", "SIZE", 4.99,
              "Polyester", color="Multicolor", set_count=5,
              variants=[
                  {"sku": "TTCA-CyclingShorts-M", "size": "M", "set_count": 5},
                  {"sku": "TTCA-CyclingShorts-2XL", "size": "2XL", "set_count": 5},
              ]),
    make_task(78, "Magnetizer Tool", "充磁消磁器绿色V1", "TTCA-MagnetizerTool", "COLOR", 1.99,
              "Plastic and Steel", color="Green", set_count=1,
              variants=[{"sku": "TTCA-MagnetizerTool-Green", "color": "Green"}]),
    make_task(79, "Hex Key", "英制球形内六角扳手9件套V1", "TTCA-HexKey", "NUMBER_OF_ITEMS", 4.99,
              "Chrome Vanadium Steel", color="Green", set_count=9,
              variants=[{"sku": "TTCA-HexKey-9pcs", "set_count": 9}]),
    make_task(81, "Repair Kit", "电讯维修批组套23件套V1", "TTCA-RepairKit", "NUMBER_OF_ITEMS", 3.99,
              "Steel and Plastic", color="Green", set_count=23,
              variants=[{"sku": "TTCA-RepairKit-23pcs", "set_count": 23}]),
    make_task(82, "Hair Tie", "蝴蝶结金色银色V1", "TTCA-HairTie", "COLOR/SET_NAME", 1.99,
              "Metal", set_count=1,
              variants=[
                  {"sku": "TTCA-HairTie-DoubleArc-Gold", "color": "Gold", "set_name": "Double Arc"},
                  {"sku": "TTCA-HairTie-Bow-Silver", "color": "Silver", "set_name": "Bow"},
                  {"sku": "TTCA-HairTie-Bow-Gold", "color": "Gold", "set_name": "Bow"},
                  {"sku": "TTCA-HairTie-DoubleArc-Silver", "color": "Silver", "set_name": "Double Arc"},
              ]),
    make_task(86, "Sport Socks", "短袜5双装V1", "TTCA-SportSocks", "NUMBER_OF_ITEMS", 2.99,
              "Polyester Blend", color="Multicolor", set_count=5,
              variants=[{"sku": "TTCA-SportSocks-5pairs", "set_count": 5}]),
    make_task(87, "Mesh Strainer", "过滤网200目V1", "TTCA-MeshStrainer", "SIZE", 1.99,
              "Nylon and Plastic", color="White", size="200 Mesh", set_count=1,
              variants=[{"sku": "TTCA-MeshStrainer-200mesh", "size": "200 Mesh"}]),
    make_task(88, "Boat Socks", "船袜7双装V1", "TTCA-BoatSocks", "NUMBER_OF_ITEMS", 2.99,
              "Polyester Blend", color="Multicolor", set_count=7,
              variants=[{"sku": "TTCA-BoatSocks-7pairs", "set_count": 7}]),
    make_task(91, "Rug Gripper", "防滑贴16件装V1", "TTCA-RugGripper", "NUMBER_OF_ITEMS", 1.99,
              "Polyurethane", color="Black", set_count=16,
              variants=[{"sku": "TTCA-RugGripper-16pcs", "set_count": 16}]),
    make_task(92, "Marking Ruler", "直尺红色V1", "TTCA-MarkingRuler", "COLOR", 2.99,
              "Aluminum", color="Red", size="30 CM", set_count=1,
              variants=[{"sku": "TTCA-MarkingRuler-Red", "color": "Red", "size": "30 CM"}]),
    make_task(93, "Exercise Band", "拉力带V1", "TTCA-ExerciseBand", "NUMBER_OF_ITEMS", 4.99,
              "Rubber", color="Multicolor", set_count=1,
              variants=[{"sku": "TTCA-ExerciseBand-1pc", "set_count": 1}],
              base_title="Resistance Band for Pull Up Assistance, Stretching, Strength Training, Mobility and Fitness Workouts, Multicolor"),
    make_task(94, "Leather Punch", "皮革打孔器V1", "TTCA-LeatherPunch", "NUMBER_OF_ITEMS", 4.99,
              "Steel", color="Red", set_count=1,
              variants=[{"sku": "TTCA-LeatherPunch-1pc", "set_count": 1}]),
    make_task(95, "Bottle Opener", "开瓶器3件装V1", "TTCA-BottleOpener", "NUMBER_OF_ITEMS", 1.99,
              "Plastic and Metal", color="Multicolor", set_count=3,
              variants=[{"sku": "TTCA-BottleOpener-3pcs", "set_count": 3}]),
    make_task(96, "Magnetic Mount", "磁吸手机支架V1", "TTCA-MagneticMount", "NUMBER_OF_ITEMS", 2.99,
              "Plastic and Metal", color="Black", set_count=1,
              variants=[{"sku": "TTCA-MagneticMount-1pc", "set_count": 1}]),
    make_task(97, "Shoe Bag", "洗鞋袋黄色V1", "TTCA-ShoeBag", "COLOR", 2.99,
              "Polyester", color="Yellow", set_count=1,
              variants=[{"sku": "TTCA-ShoeBag-Yellow", "color": "Yellow"}]),
    make_task(101, "Laundry Bag", "鞋子清洗袋白色V1", "TTCA-LaundryBag", "COLOR", 2.99,
              "Polyester", color="White", set_count=1,
              variants=[{"sku": "TTCA-LaundryBag-White", "color": "White"}]),
    make_task(106, "Snap Hook", "搭扣20件装40毫米V1", "TTCA-SnapHook", "COLOR/SIZE/NUMBER_OF_ITEMS", 2.99,
              "Metal", color="Silver", size="40 MM", set_count=20,
              variants=[{"sku": "TTCA-SnapHook-20pcs-40mm", "color": "Silver", "size": "40 MM", "set_count": 20}]),
    make_task(110, "Phone Pouch", "手机防水袋黑色白色V1", "TTCA-PhonePouch", "COLOR", 2.99,
              "PVC", set_count=1,
              variants=[
                  {"sku": "TTCA-PhonePouch-White", "color": "White"},
                  {"sku": "TTCA-PhonePouch-Black", "color": "Black"},
              ],
              base_title="Floating Phone Pouch with Clear Touch Screen, Dry Bag Case for Beach, Swimming, Boating and Travel"),
    make_task(112, "Dog Toy", "狗玩具组合款V1", "TTCA-DogToy", "SET_NAME", 3.49,
              "Cotton", color="Multicolor", set_count=1,
              variants=[
                  {"sku": "TTCA-DogToy-BallSet-2pcs", "set_name": "2 Piece Ball Set", "set_count": 2, "price": 2.99},
                  {"sku": "TTCA-DogToy-MixedSet-3pcs", "set_name": "3 Piece Mixed Set", "set_count": 3, "price": 3.99},
                  {"sku": "TTCA-DogToy-RopeKnot-1pc", "set_name": "1 Piece Long Rope Knot", "set_count": 1, "price": 4.91},
              ],
              extra_fields={"subject_character[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value": "Dog"},
              parent_extra_fields={"subject_character[marketplace_id=ATVPDKIKX0DER][language_tag=en_US]#1.value": "Dog"}),
    make_task(115, "Cherry Charm", "樱桃挂饰红色V1", "TTCA-CherryCharm", "COLOR", 1.99,
              "Faux Leather and Metal", color="Red", set_count=1,
              variants=[{"sku": "TTCA-CherryCharm-Red", "color": "Red"}]),
    make_task(116, "Crystal Bracelet", "手链珍珠款V1", "TTCA-CrystalBracelet", "COLOR", 2.99,
              "Crystal and Imitation Pearl", color="Pearl", set_count=1,
              variants=[{"sku": "TTCA-CrystalBracelet-Pearl", "color": "Pearl"}]),
    make_task(117, "Incense Holder", "蚊香支架V1", "TTCA-IncenseHolder", "NUMBER_OF_ITEMS", 2.99,
              "Stainless Steel", color="Silver", set_count=1,
              variants=[{"sku": "TTCA-IncenseHolder-1pc", "set_count": 1}]),
    make_task(118, "Scarf Ring", "衣角扣子3件装V1", "TTCA-ScarfRing", "NUMBER_OF_ITEMS", 2.49,
              "Metal", color="Silver", set_count=3,
              variants=[{"sku": "TTCA-ScarfRing-3pcs", "set_count": 3}]),
    make_task(119, "Capybara Keychain", "卡皮巴拉钥匙扣3件装V1", "TTCA-CapybaraKeychain", "NUMBER_OF_ITEMS", 2.99,
              "PVC", color="Multicolor", set_count=3,
              variants=[{"sku": "TTCA-CapybaraKeychain-3pcs", "set_count": 3}]),
    make_task(122, "Resin Keychain", "钥匙扣木色V1", "TTCA-ResinKeychain", "COLOR", 1.99,
              "Resin, Faux Leather and Metal", color="Wood", set_count=1,
              variants=[{"sku": "TTCA-ResinKeychain-Wood", "color": "Wood"}]),
    make_task(124, "Baking Paper", "方形烘焙纸50张V1", "TTCA-BakingPaper", "SIZE/NUMBER_OF_ITEMS", 1.45,
              "Paper", color="Brown", size="8 x 6 Inches", set_count=50,
              variants=[{"sku": "TTCA-BakingPaper-50pcs", "size": "8 x 6 Inches", "set_count": 50}],
              base_title="50 Pcs Square Parchment Paper Sheets, 8 x 6 Inch Nonstick Baking Liners for Air Fryer, Oven and Cooking"),
]


manifest = {
    "batch_name": "Cady退货翻新第三批",
    "output_dir": "../outputs",
    "tasks": tasks,
}
(ROUND_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {len(tasks)} tasks to {ROUND_DIR / 'manifest.json'}")
