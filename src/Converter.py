import json5, shutil, os, json
from preconditiontogsq import convert as preconditiontogsq

from .Logger import logger
from .Utils import (
    inventoryTypeToQualified,
)

class Converter:
    manifest: dict = {}
    shops: dict = {}
    content: dict = {
        "Format": "2.0",
        "Changes": []
    }
    
    def __init__(self):
        self.manifest = json5.load(open('input/manifest.json', encoding='utf8'))
        self.shops = json5.load(open('input/shops.json', encoding='utf8'))

        if os.path.exists('output'):
            shutil.rmtree('output')
        shutil.copytree('input', 'output')

    def convert(self):
        if 'AnimalShops' in self.shops:
            logger.error(f'AnimalsShop(s) ({", ".join([x["ShopName"] for x in self.shops["AnimalShops"] ])}) found in shops.json, will be ignored.')
        
        for shop in self.shops['Shops']:
            logger.info(shop)
            shopID = f'{self.manifest["UniqueID"]}_{shop["ShopName"]}'
            
            gsq = None
            portrait = None
            if 'When' in shop:
                gsq = ''
                for w in shop['When']:
                    gsq += preconditiontogsq(w)

            if 'PortraitPath' in shop:
                portraitAssetsPath = shop['PortraitPath']

                portrait = f"Portraits/{shopID}_Portrait"

                self.content['Changes'].append({
                    "Action": "Load",
                    "Target": portrait,
                    "FromFile": portraitAssetsPath,
                })
            
            shopCondition = gsq

            _items = []
            for index, _item in enumerate(shop['ItemStocks']):

                if 'ItemIDs' not in _item:
                    logger.error(f'No ItemIDs found for item {index} of {shopID}')
                    continue

                item = {
                    "Id": f"{shopID}_Item_{index}",
                    "Price": _item['StockPrice'],
                    "ItemId": f'{inventoryTypeToQualified(_item["ItemType"])}{_item["ItemIDs"][0]}' # idk why there are multiple items, that's for future me to fix.
                }
                
                if 'Stock' in _item:
                    item['AvailableStock'] = _item['Stock']

                if 'When' in _item:
                    condition_list = []
                    for w in _item['When']:
                        condition_list.append(preconditiontogsq(w))

                    _condition_str = '" "'.join(condition_list)
                    item['Condition'] = f'ANY "{_condition_str}"'
                _items.append(item)


            entry = {
                shopID: {
                    "Owners": [
                        { # Closed
                            "Condition": f"!{shopCondition}",
                            "Portait": None,
                            "Dialogues": None,
                            "ClosedMessage": shop['ClosedMessage'] if \
                                'ClosedMessage' in shop else 'This shop is closed.',
                            "Id": f'{shopID}-ClosedOwner',
                            "Name": "AnyOrNone",
                        },
                        { # Open
                            "Condition": shopCondition,
                            "Portrait": portrait,
                            "Dialogues": [
                                {
                                    "Id": f'{shopID}-OpenOwnerDialogue',
                                    "Dialogue": shop['Quote'] if 'Quote' in shop else None
                                }
                            ],
                            "ClosedMessage": None,
                            "Id": f'{shopID}-OpenOwner',
                            "Name": "AnyOrNone",
                        },
                    ],
                    "Items": _items
                }
            }

            change = {
                "Action": "EditData",
                "Target": "Data/Shops",
                "Entries": entry
            }

            self.content['Changes'].append(change)



        self.translateManifest()
        self.save()


    def translateManifest(self):
        self.manifest['UniqueID'] += '.CP'
        self.manifest['Author'] += ' ~ STF2CP'

        self.manifest['ContentPackFor']['UniqueID'] = 'Pathoschild.ContentPatcher'
        if 'Dependencies' in self.manifest:
            self.manifest['Dependencies'] = \
                [mod for mod in self.manifest['Dependencies'] if mod['UniqueID'] not in ['Cherry.ShopTileFramework']]
        
    def save(self):
        
        with open('output/manifest.json', 'w') as f:
            json.dump(self.manifest, f, indent=4)
        
        with open('output/content.json', 'w') as f:
            json.dump(self.content, f, indent=4)

        os.remove('output/shops.json')