import csv
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#Function that was just useful for converting a existing spreadsheet, keeping as a utility function.
def csvToDict(file_name):
    with open(file_name, mode='r') as infile:
        reader = csv.reader(infile)
        mydict = {rows[0]:rows[1] for rows in reader}
    return mydict

#This used to be a csv, but it seemed better because it is rather small.
#The textstring is a google maps place id from here: https://developers-dot-devsite-v2-prod.appspot.com/maps/documentation/javascript/examples/places-placeid-finder
#I am doing it this way because simply sending the string "Rhode Island" to google maps does not return very accurate numbers,
locations = {
'Old Dominion': 'ChIJuzI_WlWYuokR32Rcvevo1rs',
"St. Mary's": 'ChIJ3w4HnXHguYkROdsJO529Ijo',
'Georgetown': 'ChIJ-4YJCMWwt4kRzSydj7z1Ue0',
'Navy': 'ChIJeRmqlzX2t4kR3qi5uYkYeDs',
'NY Maritime': 'ChIJu2t-5v-KwokRSEfV3bZjkWM',
'MIT': 'ChIJiWvSN6hw44kR0opwGkt012Y',
'Brown/Dartmouth': 'ChIJKziuJ3yl5YkRi0MYTQsCW54',
'Coast Guard': 'ChIJg5vO5tUN5okRU0FK938AOJA',
'Kings Point': 'ChIJp2uRacWLwokRhUHVSSFid0Q',
'Brown': 'ChIJYx4Dlt1P5IkRbpMrj0e6f8g',
'Rhode Island': 'ChIJ6Rju90y55YkRUwM5QWqLxOQ',
'Hobart & William Sm': 'ChIJDarTARzF0IkR8CpymncFIU0',
'Cornell': 'ChIJh5EVqMqD0IkR1gXM1-zJbQw',
'Yale': 'ChIJp8HXAYB46IkRmnknByNkn_c',
'Charleston': 'ChIJde2n_zV6_ogRW3bRgY2nL3c',
'Connecticut College': 'ChIJJaWq8dAN5okRWWEZ5yDW6tw',
'Boston University': 'ChIJKW7kW-V544kRLIt3IaRJ3q0',
'Hampton': 'ChIJC88Q9LeEuokRRfowf8_u-xQ',
'George Washington': 'ChIJ-4YJCMWwt4kRzSydj7z1Ue0',
'Grand Valley State': 'ChIJA1C7WPL0GYgRXMoc34Y3M8M',
'Washington College': 'ChIJ5Z1f6kCLx4kRHnzOogC92Fg',
'Southern Cal': 'ChIJV3jYm0gw3YAR556zsW6Qi6k',
'Texas A&M Galveston': 'ChIJb4Pc544sRIYRaHCs0_eFozM',
'Stanford': 'ChIJQXp0gI6ij4ARd5xmGUQ4gRs',
'Berkeley':"ChIJT80BLy6AhYARE3tHDpaz14w",
'Hawaii': "ChIJ3_mrhFZuAHwRDS-Xa_gkESY",
'South Florida': "ChIJoUPDPRThwogR-FeTAczlAxE",
'Dartmouth': 'ChIJSXdvx0eytEwRISHbAYPOuTY',
'Tufts': 'ChIJKWBOhu5244kRoAu9xXl8pyU',
'Tulane': "ChIJj6e0zVOuIIYRJXH1AmXP4fQ",
'Roger Williams': 'ChIJZU4JQfJU5IkRFXT-9q9th8M',
'UC Santa Barbara':"ChIJdd5-rfQT6YARm-1h8EOR8uI",
'Fordham': "ChIJr4yli4WLwokRVPXA-k-6Sqs",
'Boston College/MIT':'ChIJiWvSN6hw44kR0opwGkt012Y',
'San Diego State':'ChIJc_Ttn4ZW2YARXlBazDX52z8',
'Cal Poly':'ChIJWcxAKZ3h7IARUasiGfna2_M',

}

def get(location):
    if location in locations:
        return locations[location]
    else:
        #if the location doesnt exist above, we log a warning.
        logger.warning(location)
        return False
