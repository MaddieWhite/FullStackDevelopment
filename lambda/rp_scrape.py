#This is a function I'm still writing that gets the sailors rp data so I can attribute races to sailors.

from bs4 import BeautifulSoup
import copy, requests, re


def regatta_scrape(regattaLink):
    url = "https://scores.collegesailing.org" + regattaLink + "sailors/"
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')

    parentDict = {}
    childDict = {}
    c = counter()

    tableBody = soup.find_all("table", class_="coordinate sailors")
    print(tableBody)

    # trArray = tableBody.find_all("tr")
    #
    # for tr in trArray:
    #     if c.counter == 1 or c.counter ==2:
    #         if c.counter == 1:
    #             teamName = tr.a.text
    #         tempArray = []
    #         scoresList = tr.find_all("td", class="right")
    #         for score in scoresList:
    #             try:
    #                 tempArray.append(int(score.text))
    #             except:
    #                 alt = score.get("title")
    #                 alt = int(re.search(r'\((\d*),', alt).group(1))
    #                 tempArray.append(alt)
    #                 print(alt)
    #         tempArray.pop(-1)
    #         if(c.counter == 1):
    #             childDict['aDiv'] = tempArray
    #         else:
    #             childDict['bDiv'] = tempArray
    #         c.inc()
    #     elif c.counter == 3:
    #         childDict['place'] = c.total
    #         parentDict[teamName] = copy.deepcopy(childDict)
    #         c.inc()
    #         continue
    # return parentDict

class counter:
    def __init__(self):
        self.total = 1
        self.counter = 1

    def inc(self):
        if self.counter == 1:
            self.counter = 2
        elif self.counter == 2:
            self.counter = 3
        elif self.counter == 3:
            self.total += 1
            self.counter = 1


print(regatta_scrape("/f19/victorian-urn/"))
