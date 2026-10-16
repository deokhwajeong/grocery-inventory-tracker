"""
Curated catalog of common grocery products used to normalize receipt names.

Receipts print names like "ORG BNNA", "GRND BEEF 80/20" or "KS WHL MLK 1GAL".
The normalizer in ocr_advanced.py strips codes and sizes, expands the
shorthand below, and then looks the result up here, so the inventory shows
"Bananas", "Ground Beef" and "Whole Milk" with the right category.

The list was written by hand from everyday grocery vocabulary. It is not
scraped from any retailer. Each line is

    Canonical Name: variant, variant, ...

Variants cover other spellings, common receipt forms, brand name spelling
differences (for example "coca cola", "coca-cola", "coke") and the
romanized Korean names the app already understood. Plural and singular forms
match automatically, so they are not listed.
"""
import re
from typing import Dict, Optional, Tuple

_CATALOG_TEXT = {
    "Dairy": """
Milk: uyu, milkeu, melk
Whole Milk: vitamin d milk, homogenized milk, whole milk gallon
2% Milk: reduced fat milk, 2 percent milk, 2pct milk
1% Milk: low fat milk, lowfat milk, 1 percent milk
Skim Milk: fat free milk, nonfat milk, non fat milk
Lactose Free Milk: lactose-free milk, lf milk
Chocolate Milk: choc milk
Oat Milk: oatmilk, oat beverage
Almond Milk: almondmilk, almond beverage
Soy Milk: soymilk, dubu milk
Buttermilk: cultured buttermilk
Half and Half: half & half, half n half
Heavy Cream: heavy whipping cream, whipping cream
Whipped Cream: whip cream, whipped topping
Sour Cream: soured cream
Cream Cheese: cream chs
Cottage Cheese: small curd cottage cheese
Ricotta Cheese: ricotta
Cheese: chijeu, chiijeu, cheeze
Cheddar Cheese: cheddar, sharp cheddar, mild cheddar
Mozzarella Cheese: mozzarella, fresh mozzarella
Parmesan Cheese: parmesan, parmigiano reggiano, grated parmesan
Swiss Cheese: swiss
Provolone Cheese: provolone
Monterey Jack Cheese: monterey jack
Pepper Jack Cheese: pepper jack
Colby Jack Cheese: colby jack
American Cheese: american singles, cheese singles
Feta Cheese: feta, crumbled feta
Goat Cheese: chevre
Brie Cheese: brie
Gouda Cheese: gouda
Blue Cheese: bleu cheese, blue cheese crumbles
Shredded Mexican Cheese: mexican blend cheese, shredded mexican blend
String Cheese: mozzarella sticks snack, cheese sticks
Yogurt: yogeoteu, yogureuteu, yoghurt, yogourt
Greek Yogurt: greek yoghurt, greek style yogurt
Plain Yogurt: natural yogurt
Vanilla Yogurt: vanilla yoghurt
Strawberry Yogurt: strawberry yoghurt
Kefir: milk kefir
Unsalted Butter: sweet cream butter unsalted
Salted Butter: butter salted
Butter: beoteo
Margarine: vegetable spread
Ghee: clarified butter
Egg: gyeran, egeu, ran
Large Eggs: lg eggs, grade a large eggs, dozen eggs
Extra Large Eggs: xl eggs
Brown Eggs: cage free brown eggs
Egg Whites: liquid egg whites
Coffee Creamer: creamer, non dairy creamer
""",
    "Meat": """
Chicken: dalgogi, chikin, chiken
Chicken Breast: boneless chicken breast, chicken breasts boneless skinless, bnls skls chicken breast
Chicken Thighs: boneless chicken thighs
Chicken Drumsticks: drumsticks
Chicken Wings: wings, party wings
Whole Chicken: whole fryer
Ground Chicken: minced chicken
Rotisserie Chicken: roast chicken
Chicken Tenders: chicken tenderloins
Beef: sogogi, bipeu, beaf
Ground Beef: minced beef, hamburger meat, ground chuck
Lean Ground Beef: extra lean ground beef, 93/7 ground beef
Ribeye Steak: rib eye steak, ribeye
Sirloin Steak: top sirloin, sirloin
New York Strip Steak: ny strip, strip steak
Flank Steak: flank
Beef Stew Meat: stew meat, stew beef
Chuck Roast: beef chuck roast, pot roast
Beef Brisket: brisket
Short Ribs: beef short ribs, galbi
Bulgogi Beef: bulgogi
Ground Turkey: minced turkey
Turkey Breast: roast turkey breast
Sliced Turkey: deli turkey, turkey lunch meat
Pork: dwaejigogi, pokeu, prok
Pork Chops: pork loin chops, bone in pork chops
Pork Tenderloin: tenderloin pork
Pork Shoulder: pork butt, boston butt
Pork Belly: samgyeopsal
Ground Pork: minced pork
Baby Back Ribs: pork ribs, spare ribs
Bacon: thick cut bacon, sliced bacon
Turkey Bacon: bacon turkey
Ham: spiral ham, ham steak
Sliced Ham: deli ham, ham lunch meat
Breakfast Sausage: sausage links, sausage patties
Italian Sausage: sweet italian sausage, hot italian sausage
Bratwurst: brats
Hot Dogs: franks, frankfurters, beef franks
Pepperoni: sliced pepperoni
Salami: genoa salami
Prosciutto: prosciutto di parma
Roast Beef: deli roast beef
Lamb Chops: lamb loin chops
Ground Lamb: minced lamb
Salmon Fillet: salmon, atlantic salmon, salmon filet
Smoked Salmon: lox
Tilapia Fillet: tilapia
Cod Fillet: cod
Halibut Fillet: halibut
Catfish Fillet: catfish
Shrimp: prawns, raw shrimp, cooked shrimp
Tuna Steak: ahi tuna
Scallops: sea scallops
Crab Meat: lump crab
Lobster Tail: lobster
Mussels: fresh mussels
""",
    "Produce": """
Apples: apple bag, sagwa, aepeul, aple
Honeycrisp Apples: honeycrisp
Gala Apples: gala
Fuji Apples: fuji
Granny Smith Apples: granny smith
Bananas: banana bunch, beonana, bananna
Oranges: orange bag
Navel Oranges: navel
Mandarins: clementines, cuties, tangerines
Lemons: lemon
Limes: lime
Grapefruit: ruby red grapefruit
Grapes: seedless grapes
Red Grapes: red seedless grapes
Green Grapes: green seedless grapes
Strawberries: strawberry
Blueberries: blueberry
Raspberries: raspberry
Blackberries: blackberry
Cherries: sweet cherries
Peaches: yellow peaches
Nectarines: nectarine
Plums: black plums
Pears: bartlett pears, bosc pears
Asian Pears: bae, korean pear
Mangoes: mango
Pineapple: whole pineapple
Watermelon: seedless watermelon
Cantaloupe: muskmelon
Honeydew Melon: honeydew
Kiwi: kiwifruit
Papaya: papayas
Pomegranate: pomegranates
Avocados: avocado, hass avocado
Tomatoes: vine tomatoes, tomatoes on the vine, tomeyito, tomatoe
Cherry Tomatoes: cherry tomato
Roma Tomatoes: roma tomato
Grape Tomatoes: grape tomato
Potatoes: potato bag, gamja, poteyito, potatoe
Russet Potatoes: russet
Red Potatoes: red potato
Yukon Gold Potatoes: yukon gold
Sweet Potatoes: sweet potato, yams, goguma
Onions: onion bag, yangpa, eonieon, oinion
Yellow Onions: yellow onion
Red Onions: red onion
White Onions: white onion
Green Onions: scallions, spring onions, pa
Shallots: shallot
Garlic: garlic bulb, maneul
Ginger: ginger root
Carrots: carrot bag, danggeun, kaeret, carott
Baby Carrots: baby carrot
Celery: celery stalks
Broccoli: broccoli crowns
Cauliflower: cauliflower head
Cabbage: kaebiji, cabage, green cabbage
Napa Cabbage: baechu, chinese cabbage
Red Cabbage: purple cabbage
Brussels Sprouts: brussel sprouts
Kale: curly kale, lacinato kale
Spinach: sigeumchi
Baby Spinach: baby spinach leaves
Romaine Lettuce: romaine, romaine hearts
Iceberg Lettuce: iceberg
Lettuce: sangchu
Spring Mix: mixed greens, salad greens
Arugula: rocket
Cucumber: cucumbers, oi
Zucchini: courgette, hobak
Yellow Squash: summer squash
Butternut Squash: butternut
Spaghetti Squash: spaghetti squash
Pumpkin: pie pumpkin
Bell Peppers: bell pepper
Red Bell Pepper: red pepper
Green Bell Pepper: green pepper
Yellow Bell Pepper: yellow pepper
Jalapeno Peppers: jalapeno, jalapenos
Mushrooms: mushroom
White Mushrooms: button mushrooms
Portobello Mushrooms: portobello
Shiitake Mushrooms: shiitake
Asparagus: asparagus bunch
Green Beans: string beans
Snap Peas: sugar snap peas, snow peas
Corn on the Cob: sweet corn, corn ears
Eggplant: aubergine, gaji
Beets: beet
Radishes: radish
Daikon Radish: daikon, mu
Turnips: turnip
Parsnips: parsnip
Leeks: leek
Fennel: fennel bulb
Artichokes: artichoke
Okra: fresh okra
Bok Choy: baby bok choy
Bean Sprouts: kongnamul, mung bean sprouts
Cilantro: coriander
Parsley: flat leaf parsley
Basil: fresh basil
Fresh Mint: mint leaves
Dill: fresh dill
Rosemary: fresh rosemary
Thyme: fresh thyme
Perilla Leaves: kkaennip
Tofu: dubu, bean curd, firm tofu, soft tofu
Tempeh: tempe
Coleslaw Mix: slaw mix
Salad Kit: chopped salad kit
Dates: medjool dates
Figs: fresh figs
Coconut: whole coconut
Plantains: plantain
Persimmons: persimmon, gam
Apricots: apricot
Cranberries: fresh cranberries
""",
    "Bakery": """
Bread: ppang, beu-re-deu, bred, loaf
White Bread: sandwich bread
Whole Wheat Bread: wheat bread, 100% whole wheat
Multigrain Bread: multi grain bread, seeded bread
Sourdough Bread: sourdough, sourdough loaf
Rye Bread: rye
Baguette: french bread
Ciabatta: ciabatta rolls
Brioche: brioche buns
Bagels: bagel, plain bagels, everything bagels
English Muffins: english muffin
Croissants: croissant, butter croissants
Dinner Rolls: rolls
Hamburger Buns: burger buns
Hot Dog Buns: hotdog buns
Hoagie Rolls: sub rolls
Pita Bread: pita
Naan: naan bread
Flour Tortillas: tortillas
Corn Tortillas: corn tortilla
Muffins: muffin
Blueberry Muffins: blueberry muffin
Donuts: doughnuts, glazed donuts
Cinnamon Rolls: cinnamon buns
Danish: danish pastry
Cake: keikeu
Cupcakes: cupcake
Bakery Cookies: fresh baked cookies
Pie: apple pie, pumpkin pie
Banana Bread: banana loaf
Biscuits: buttermilk biscuits
""",
    "Frozen": """
Ice Cream: aiseukeurim, ice-cream, icecream
Vanilla Ice Cream: vanilla icecream
Chocolate Ice Cream: chocolate icecream
Frozen Yogurt: froyo
Ice Pops: popsicles, fruit bars frozen
Frozen Pizza: pizza
Frozen Peas: peas frozen, green peas
Frozen Corn: corn frozen
Frozen Broccoli: broccoli florets frozen
Frozen Spinach: chopped spinach frozen
Frozen Mixed Vegetables: mixed vegetables, mixed veggies
Frozen Green Beans: green beans frozen
Frozen Edamame: edamame
Frozen Berries: mixed berries frozen
Frozen Blueberries: blueberries frozen
Frozen Strawberries: strawberries frozen
Frozen Mango: mango chunks frozen
French Fries: frozen fries, fries
Hash Browns: hashbrowns, shredded hash browns
Tater Tots: potato tots
Frozen Waffles: waffles
Frozen Pancakes: pancakes frozen
Fish Sticks: fish fingers
Frozen Shrimp: shrimp frozen
Chicken Nuggets: nuggets
Frozen Burritos: burritos
Frozen Dumplings: dumplings, mandu, potstickers, gyoza
Frozen Meals: frozen dinner, tv dinner
Frozen Lasagna: lasagna frozen
Frozen Meatballs: meatballs
Veggie Burgers: plant based burgers
Pie Crust: frozen pie crust
Puff Pastry: puff pastry sheets
Ice: bagged ice, ice bag
Garlic Bread: frozen garlic bread
Cauliflower Rice: riced cauliflower
""",
    "Pantry": """
Rice: ssal, grain
White Rice: long grain white rice
Brown Rice: whole grain brown rice
Basmati Rice: basmati
Jasmine Rice: jasmine
Short Grain Rice: sushi rice, calrose rice
Quinoa: white quinoa
Couscous: pearl couscous
Pasta: dry pasta
Spaghetti: spaghetti pasta
Penne Pasta: penne
Macaroni: elbow macaroni, elbows
Fettuccine: fettuccini
Linguine: linguini
Rotini: rotini pasta
Egg Noodles: wide egg noodles
Lasagna Noodles: lasagne
Ramen: ramyeon, instant noodle, instant noodles, ramen noodles
Rice Noodles: pho noodles
Udon Noodles: udon
Soba Noodles: soba
Glass Noodles: dangmyeon, sweet potato noodles
Macaroni and Cheese: mac and cheese, mac n cheese, mac & cheese
All Purpose Flour: ap flour, flour
Bread Flour: unbleached bread flour
Whole Wheat Flour: wheat flour
Granulated Sugar: sugar, white sugar, cane sugar
Brown Sugar: light brown sugar, dark brown sugar
Powdered Sugar: confectioners sugar, icing sugar
Baking Soda: bicarbonate of soda
Baking Powder: double acting baking powder
Yeast: active dry yeast, instant yeast
Vanilla Extract: pure vanilla extract
Cornstarch: corn starch
Cocoa Powder: unsweetened cocoa
Chocolate Chips: semi sweet chocolate chips, choc chips
Pancake Mix: pancake and waffle mix
Maple Syrup: pure maple syrup, pancake syrup
Honey: clover honey, raw honey
Peanut Butter: creamy peanut butter, crunchy peanut butter
Almond Butter: almond spread
Strawberry Jam: strawberry preserves, jam
Grape Jelly: jelly
Hazelnut Spread: chocolate hazelnut spread
Olive Oil: extra virgin olive oil, evoo
Vegetable Oil: veg oil
Canola Oil: canola
Coconut Oil: virgin coconut oil
Sesame Oil: toasted sesame oil, chamgireum
Avocado Oil: avocado cooking oil
Cooking Spray: nonstick spray
White Vinegar: distilled vinegar, vinegar
Apple Cider Vinegar: cider vinegar
Balsamic Vinegar: balsamic
Rice Vinegar: rice wine vinegar
Soy Sauce: ganjang, soya sauce, low sodium soy sauce
Ketchup: catsup, tomato ketchup
Yellow Mustard: mustard
Dijon Mustard: dijon
Mayonnaise: mayo
Hot Sauce: pepper sauce
Sriracha: sriracha sauce
BBQ Sauce: barbecue sauce
Salsa: chunky salsa, medium salsa
Ranch Dressing: ranch
Italian Dressing: italian vinaigrette
Pasta Sauce: marinara, marinara sauce, spaghetti sauce, tomato basil sauce
Pesto: basil pesto
Tomato Paste: tomato puree
Tomato Sauce: canned tomato sauce
Crushed Tomatoes: canned crushed tomatoes
Diced Tomatoes: canned diced tomatoes
Chicken Broth: chicken stock
Beef Broth: beef stock
Vegetable Broth: vegetable stock, veggie broth
Black Beans: canned black beans
Kidney Beans: red kidney beans
Pinto Beans: canned pinto beans
Chickpeas: garbanzo beans
Lentils: red lentils, green lentils
Refried Beans: refried
Canned Corn: whole kernel corn, sweet corn canned
Canned Green Beans: cut green beans
Tuna: canned tuna, chunk light tuna, albacore tuna
Canned Salmon: pink salmon canned
Chicken Noodle Soup: canned soup
Tomato Soup: condensed tomato soup
Coconut Milk: canned coconut milk
Rolled Oats: old fashioned oats, oats
Instant Oatmeal: oatmeal packets, oatmeal
Cereal: breakfast cereal
Corn Flakes: cornflakes
Granola: honey granola
Bread Crumbs: breadcrumbs
Panko: panko bread crumbs
Salt: sea salt, kosher salt, table salt
Black Pepper: ground black pepper, peppercorns
Garlic Powder: granulated garlic
Onion Powder: granulated onion
Paprika: smoked paprika
Ground Cumin: cumin
Chili Powder: chile powder
Ground Cinnamon: cinnamon
Dried Oregano: oregano
Italian Seasoning: italian herbs
Red Pepper Flakes: crushed red pepper
Bay Leaves: bay leaf
Curry Powder: curry
Gochujang: red pepper paste
Gochugaru: red pepper powder
Doenjang: soybean paste
Kimchi: gimchi, kimchee
Roasted Seaweed: gim, nori, laver
Sesame Seeds: toasted sesame seeds
Fish Sauce: nam pla
Oyster Sauce: oyster flavored sauce
Hoisin Sauce: hoisin
Teriyaki Sauce: teriyaki
Pickles: dill pickles, pickle spears
Olives: black olives, kalamata olives, green olives
Capers: nonpareil capers
Sun Dried Tomatoes: sundried tomatoes
Canned Pineapple: pineapple chunks canned
Applesauce: apple sauce
Raisins: seedless raisins
Dried Cranberries: craisins
Taco Shells: hard taco shells
Taco Seasoning: taco mix
Gravy Mix: brown gravy
Stuffing Mix: stuffing
Baby Food: baby puree
""",
    "Beverages": """
Water: saengsu, woteo
Bottled Water: spring water, purified water, water bottles
Sparkling Water: seltzer, carbonated water, sparkling mineral water
Mineral Water: natural mineral water
Coconut Water: coconut drink
Orange Juice: oj, orange juice not from concentrate, fresh orange juice
Apple Juice: apple cider
Grape Juice: concord grape juice
Cranberry Juice: cranberry cocktail
Tomato Juice: vegetable juice
Lemonade: lemon drink
Iced Tea: ice tea, sweet tea
Cola: kola, kokakola
Coca-Cola: coca cola, coke, coke classic
Diet Cola: diet coke, cola zero, coke zero
Pepsi: pepsi cola
Sprite: saida, seupeuraiteu, chilseong
Lemon Lime Soda: lemon-lime soda
Ginger Ale: gingerale
Root Beer: rootbeer
Tonic Water: tonic
Club Soda: soda water
Soda: soft drink, pop
Sports Drink: electrolyte drink
Energy Drink: energy shot
Coffee: keopi, kape, cofee
Ground Coffee: coffee ground, medium roast coffee, dark roast coffee
Coffee Beans: whole bean coffee
Instant Coffee: coffee mix, instant coffee mix
Cold Brew Coffee: cold brew
Coffee Pods: k cups, coffee capsules
Tea: cha, ti, tee, tea bags
Green Tea: nokcha, matcha tea
Black Tea: english breakfast tea, earl grey
Herbal Tea: chamomile tea, peppermint tea
Barley Tea: boricha
Kombucha: fermented tea
Hot Cocoa Mix: hot chocolate mix, cocoa mix
Protein Shake: protein drink
Smoothie: fruit smoothie
Beer: maekju, bieo, beeer, lager, ale, ipa
Red Wine: cabernet sauvignon, merlot, pinot noir
White Wine: chardonnay, sauvignon blanc, pinot grigio
Sparkling Wine: prosecco, champagne
Soju: sojyu, korean-spirit
Makgeolli: rice wine
Sake: japanese rice wine
Hard Seltzer: spiked seltzer
""",
    "Snacks": """
Snack: gwaja, seunaek
Potato Chips: chips, kettle chips, potato crisps
Tortilla Chips: corn chips, tortilla crisps
Pita Chips: baked pita chips
Pretzels: pretzel twists, pretzel sticks
Popcorn: popped popcorn
Microwave Popcorn: microwave popcorn bags
Crackers: snack crackers
Saltine Crackers: saltines
Graham Crackers: grahams
Cheese Crackers: cheddar crackers
Rice Cakes: rice cake snacks
Rice Crackers: senbei
Granola Bars: granola bar, chewy granola bars
Protein Bars: protein bar
Trail Mix: nut mix
Almonds: roasted almonds, raw almonds
Cashews: roasted cashews
Peanuts: roasted peanuts
Pistachios: shelled pistachios
Walnuts: walnut halves
Pecans: pecan halves
Mixed Nuts: deluxe mixed nuts
Sunflower Seeds: sunflower kernels
Dried Mango: mango slices dried
Fruit Snacks: fruit gummies
Beef Jerky: jerky
Chocolate: chokollit, chokollet, choco
Dark Chocolate: dark chocolate bar
Milk Chocolate: milk chocolate bar
Candy: satang, sweets
Gummy Bears: gummies, gummy candy
Mints: breath mints
Chewing Gum: gum
Cookies: cookie
Chocolate Chip Cookies: choc chip cookies
Sandwich Cookies: cream filled cookies
Wafers: wafer cookies
Brownies: brownie
Pudding Cups: pudding
Gelatin Cups: jello cups
Fruit Cups: fruit cocktail cups
Hummus: houmous, hummous
Guacamole: guac
Seaweed Snack: seaweed snacks, gim snack
Veggie Straws: vegetable straws
Cheese Puffs: cheese curls
Marshmallows: mini marshmallows
""",
    "Other": """
Paper Towels: paper towel, kitchen towels
Toilet Paper: bath tissue, toilet tissue
Facial Tissues: tissues, kleenex
Napkins: paper napkins
Dish Soap: dishwashing liquid, dish liquid
Dishwasher Detergent: dishwasher pods, dishwasher tabs
Laundry Detergent: laundry pods, detergent
Fabric Softener: dryer sheets
All Purpose Cleaner: multi surface cleaner, spray cleaner
Sponges: sponge, scrub sponges
Trash Bags: garbage bags, kitchen bags
Aluminum Foil: foil, tin foil
Plastic Wrap: cling wrap, cling film
Sandwich Bags: zip bags, storage bags, freezer bags
Parchment Paper: baking paper
Hand Soap: liquid hand soap
Shampoo: hair shampoo
Conditioner: hair conditioner
Body Wash: shower gel
Toothpaste: tooth paste
Toothbrush: toothbrushes
Deodorant: antiperspirant
Razors: razor blades
Cotton Swabs: cotton buds
Diapers: nappies
Baby Wipes: wipes
Baby Formula: infant formula
Dog Food: dry dog food
Cat Food: wet cat food
Cat Litter: kitty litter
Batteries: aa batteries, aaa batteries
Light Bulbs: led bulbs
Charcoal: charcoal briquettes
Flowers: bouquet, fresh flowers
Vitamins: multivitamin
Bandages: adhesive bandages
Pain Reliever: ibuprofen, acetaminophen
""",
}

# Receipt shorthand -> full word(s). Tills squeeze names into 20 or so
# characters, so the same handful of abbreviations shows up everywhere.
ABBREVIATIONS = {
    "org": "", "orgnc": "", "organic": "", "nat": "", "natural": "",
    "chkn": "chicken", "chk": "chicken", "ckn": "chicken", "chix": "chicken",
    "bnls": "boneless", "skls": "skinless", "brst": "breast", "brt": "breast",
    "thgh": "thighs", "thg": "thighs", "drmstk": "drumsticks",
    "grnd": "ground", "grd": "ground", "gr": "ground",
    "bf": "beef", "trky": "turkey", "tky": "turkey", "prk": "pork", "chop": "chops",
    "slmn": "salmon", "flt": "fillet", "filet": "fillet", "shrmp": "shrimp", "bcn": "bacon",
    "slcd": "sliced", "sl": "sliced", "saus": "sausage", "sausg": "sausage",
    "whl": "whole", "wh": "whole", "mlk": "milk", "mk": "milk", "rf": "reduced fat", "ff": "fat free",
    "chs": "cheese", "chse": "cheese", "chdr": "cheddar", "ched": "cheddar", "mozz": "mozzarella",
    "parm": "parmesan", "shrd": "shredded", "shred": "shredded", "ctg": "cottage", "cttg": "cottage",
    "ygrt": "yogurt", "yogrt": "yogurt", "yog": "yogurt", "yogt": "yogurt", "grk": "greek",
    "btr": "butter", "bttr": "butter", "unslt": "unsalted", "uns": "unsalted", "slt": "salted",
    "lg": "large", "lrg": "large", "xl": "extra large", "egg": "eggs", "dz": "", "doz": "", "dozen": "",
    "crm": "cream", "hvy": "heavy", "hvywhp": "heavy cream", "sr": "sour", "whp": "whipping",
    "bnna": "bananas", "bnn": "bananas", "ban": "bananas", "bana": "bananas",
    "appl": "apples", "apl": "apples", "hnycrsp": "honeycrisp", "avo": "avocados", "avoc": "avocados",
    "strwb": "strawberries", "strwbry": "strawberries", "strawb": "strawberries", "stbry": "strawberries",
    "blub": "blueberries", "blueb": "blueberries", "blubry": "blueberries", "rasp": "raspberries",
    "lttc": "lettuce", "let": "lettuce", "lett": "lettuce", "rom": "romaine", "spnch": "spinach", "spin": "spinach",
    "broc": "broccoli", "brcli": "broccoli", "caul": "cauliflower", "cuc": "cucumber", "cuke": "cucumber",
    "zuc": "zucchini", "mshrm": "mushrooms", "mush": "mushrooms", "asprg": "asparagus",
    "crt": "carrots", "carr": "carrots", "cel": "celery", "grlc": "garlic", "onin": "onions", "onn": "onions",
    "pot": "potatoes", "pots": "potatoes", "pto": "potatoes", "swt": "sweet", "tom": "tomatoes", "toms": "tomatoes",
    "ylw": "yellow", "yel": "yellow", "grn": "green", "rd": "red", "wht": "white", "bp": "bell pepper",
    "brd": "bread", "bread": "bread", "srdgh": "sourdough", "sdough": "sourdough", "wwht": "whole wheat",
    "mltgrn": "multigrain", "bgl": "bagels", "bgls": "bagels", "crsnt": "croissants", "eng": "english",
    "mfn": "muffins", "muffin": "muffins", "tort": "tortilla", "tortl": "tortillas",
    "frzn": "frozen", "frz": "frozen", "fz": "frozen", "veg": "vegetable", "vegs": "vegetables",
    "van": "vanilla", "choc": "chocolate", "ic": "ice cream", "pza": "pizza", "wffl": "waffles", "waffle": "waffles",
    "bsmti": "basmati", "bsmt": "basmati", "jsmn": "jasmine", "spag": "spaghetti", "spgti": "spaghetti",
    "psta": "pasta", "pst": "pasta", "crshd": "crushed", "crsh": "crushed", "dcd": "diced",
    "pnt": "peanut", "pb": "peanut butter", "olv": "olive", "evoo": "extra virgin olive oil",
    "bns": "beans", "blk": "black", "brth": "broth", "rld": "rolled", "purp": "purpose", "ap": "all purpose",
    "flr": "flour", "gran": "granulated", "sug": "sugar", "ktchp": "ketchup", "mayo": "mayonnaise",
    "oj": "orange juice", "jce": "juice", "jc": "juice", "jus": "juice", "aj": "apple juice",
    "cof": "coffee", "cfe": "coffee", "gnd": "ground", "spkl": "sparkling", "sprkl": "sparkling",
    "spk": "sparkling", "wtr": "water", "btl": "bottled", "btld": "bottled", "lmnd": "lemonade",
    "chps": "chips", "chp": "chips", "tor": "tortilla", "prtzl": "pretzels", "prtz": "pretzels",
    "grnla": "granola", "gran bar": "granola bars", "bar": "bars", "almd": "almonds", "hmms": "hummus",
    "ppr": "paper", "twl": "towels", "twls": "towels", "dsh": "dish", "det": "detergent", "lndry": "laundry",
    "tp": "toilet paper", "tiss": "tissues", "trsh": "trash", "bgs": "bags",
    "hny": "honey", "pk": "", "pack": "", "ct": "", "ea": "", "each": "", "pulp": "", "no": "",
}

# Store-brand and marketing words that come before the product name.
NOISE_PREFIXES = {"ks", "kirk", "kirkland", "gv", "store", "brand", "hm", "365", "sig", "great", "value",
                  "fresh", "premium", "select", "farm", "family", "pack", "value", "club"}

_SIZE_TOKEN = re.compile(
    r"^(\d+([./]\d+)?(%|pct)?|\d+([.]\d+)?(oz|fl|floz|lb|lbs|g|kg|ml|l|ltr|gal|qt|pt|ct|pk|ea|dz)|"
    r"(oz|fl|floz|lb|lbs|g|kg|ml|ltr|gal|qt|pt))$"
)


def _key(text: str) -> str:
    """Comparison key: lower case, letters and digits only, trailing plural dropped."""
    words = re.sub(r"[^a-z0-9%& ]", " ", text.lower().replace("-", " ")).split()
    if words and len(words[-1]) > 3 and words[-1].endswith("s") and not words[-1].endswith("ss"):
        words[-1] = words[-1][:-1]
    if words and words[-1].endswith("ie") and len(words[-1]) > 4:  # berries -> berrie -> berry
        words[-1] = words[-1][:-2] + "y"
    return " ".join(words)


def _build():
    products, lookup = {}, {}
    for category, block in _CATALOG_TEXT.items():
        for line in block.strip().splitlines():
            canonical, _, variants = line.partition(":")
            canonical = canonical.strip()
            products[canonical] = category
            for name in [canonical] + [v.strip() for v in variants.split(",") if v.strip()]:
                lookup.setdefault(_key(name), canonical)
    return products, lookup


PRODUCTS, LOOKUP = _build()  # canonical -> category, key -> canonical



def _bag(key: str) -> str:
    """Order-free key: every word singular, words sorted ("eggs large" == "large egg")."""
    words = [w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w for w in key.split()]
    return " ".join(sorted(words))


_UNORDERED = {}
for _k, _canonical in LOOKUP.items():
    _UNORDERED.setdefault(_bag(_k), _canonical)


def category_for(name: str) -> Optional[str]:
    """Category of a catalog product (canonical or variant name), else None."""
    canonical = LOOKUP.get(_key(name))
    return PRODUCTS.get(canonical) if canonical else None


def clean_receipt_name(raw: str) -> str:
    """Strip item codes, sizes, flags and store-brand words, and expand shorthand."""
    words = re.sub(r"[^A-Za-z0-9%&/.' -]", " ", raw).lower().replace("'", "").split()
    out = []
    for i, word in enumerate(words):
        word = word.strip(".-/")
        if not word or _SIZE_TOKEN.match(word) or re.fullmatch(r"\d{3,}", word):
            continue
        if not out and word in NOISE_PREFIXES:
            continue
        if word in ABBREVIATIONS:
            word = ABBREVIATIONS[word]
            if not word:
                continue
        out.append(word)
    return " ".join(out)


def _prefix_match(query_words, lookup_keys):
    """Match truncated words: every query word must be a prefix (3+ letters) of the candidate's word."""
    best = None
    for key in lookup_keys:
        cand = key.split()
        if len(cand) != len(query_words):
            continue
        if all(len(q) >= 3 and c.startswith(q) or q == c for q, c in zip(query_words, cand)):
            # prefer the candidate with the fewest extra letters
            extra = sum(len(c) - len(q) for q, c in zip(query_words, cand))
            if best is None or extra < best[0]:
                best = (extra, key)
    return best[1] if best else None


def match_product(raw: str, fuzzy=None) -> Tuple[Optional[str], float]:
    """
    Find the catalog product for a receipt name.

    Returns (canonical name, score 0-100) or (None, 0). ``fuzzy`` is an optional
    ratio(a, b) -> 0..100 function used as the last resort.
    """
    if not raw:
        return None, 0.0
    direct = LOOKUP.get(_key(raw))
    if direct:
        return direct, 100.0
    cleaned = clean_receipt_name(raw)
    if not cleaned:
        return None, 0.0
    key = _key(cleaned)
    if key in LOOKUP:
        return LOOKUP[key], 95.0
    words = key.split()
    unordered = _UNORDERED.get(_bag(key))
    if unordered and len(words) > 1:
        return unordered, 90.0
    hit = _prefix_match(words, LOOKUP)
    if hit:
        return LOOKUP[hit], 85.0
    fuzzy_hit = _fuzzy(key, fuzzy) if fuzzy and len(key) > 3 else None
    if fuzzy_hit:
        return fuzzy_hit
    # Drop leading words one at a time ("sweet italian sausage" -> "italian sausage")
    for start in range(1, len(words)):
        tail = " ".join(words[start:])
        if tail in LOOKUP and len(tail) > 3:
            return LOOKUP[tail], 80.0
    return None, 0.0


def _fuzzy(key, fuzzy):
    """Closest catalog key by edit similarity (catches OCR damage like "Brocolli"), or None."""
    best, best_score = None, 0
    for candidate in LOOKUP:
        if abs(len(candidate) - len(key)) > 6:
            continue
        score = fuzzy(key, candidate)
        if score > best_score:
            best, best_score = candidate, score
    if best and best_score >= 86:
        return LOOKUP[best], float(best_score) - 10
    return None


def stats() -> Dict[str, int]:
    """Number of canonical products per category."""
    out: Dict[str, int] = {}
    for category in PRODUCTS.values():
        out[category] = out.get(category, 0) + 1
    return out
