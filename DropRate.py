import PySimpleGUI as sg
import sys
import requests
from dotenv import load_dotenv
import os

#All of the different MAL rankings
topOptions = ['All', 'Airing', 'TV', 'OVA', 'Movie', 'Special', 'Popularity', 'Favorite']
optionToOption = {
    "All":"all",
    "Airing":"airing",
    "TV":"tv",
    "OVA":"ova",
    "Movie":"movie",
    "Special":"special",
    "Popularity":"bypopularity",
    "Favorite":"favorite"
}
#MAL API key
load_dotenv()

#Keep running until user exits
while True:
    #Want the window to close when another is opened and open again if the user hits "back",
    #so it's created at the beginning of the while loop
    layout = [  [sg.Text("Currently can only get drop rates, might add some other things at some point")],
                [sg.Button('Get drop rates')],
                [sg.Button('Exit')]]
    window = sg.Window('Extra MAL Stats', layout, element_justification='c')
    event, value = window.read()
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == 'Get drop rates':
        #First option - get drop rates of anime
        #Create the window before the while loop this time,
        #since it will never close and reopen before the outer while loop ends
        window.close()
        layoutDrop = [  [sg.Text('Enter an anime ID to get its drop rate: '), sg.Input(key = '-SINGLE-'), sg.Button('Submit Anime ID')],
            [sg.Text('Alternatively, get drop rates of top X anime. Allow for some time if you pick a number around or higher than 50.')],
            [sg.Text("Enter a number 1-500: "), sg.Input(size = 5, key = '-TOPX-'), sg.Text("Pick a MAL ranking: "), sg.Combo(topOptions, k='-COMBO-', default_value = "All"), sg.Checkbox("Sort by drop rate", k = '-CHECK-'), sg.Button('Sumbit top parameters')],
            [sg.Text('Results will display here: ')],
            [sg.Output(size = (100, 10), key='-OUTPUT-')],
            [sg.Button('Clear'), sg.Button('Go back'), sg.Button('Exit')]]
        windowDrop = sg.Window('Get Drop Rate', layoutDrop)

        while True:
            dropEvent, dropValue = windowDrop.read()

            if dropEvent == sg.WIN_CLOSED or dropEvent == 'Exit':
                sys.exit(0)
            elif dropEvent == 'Submit Anime ID':
                #Do input checking here later
                #Get the statistics, need Dropped/(Total Users - Plan to Watch Users)
                url = f"https://api.myanimelist.net/v2/anime/{dropValue['-SINGLE-']}?fields=statistics"
                #API key in header
                headers = {"X-MAL-CLIENT-ID" : os.environ["MALAPIKEY"]}
                response = requests.get(url, headers = headers)
                jsonr = response.json()

                #Get total users and dropped users from the response
                numtotalusers = int(jsonr['statistics']['num_list_users']) - int(jsonr['statistics']['status']['plan_to_watch'])
                droppedusers = int(jsonr['statistics']['status']['dropped'])

                #Calculate answer and convert to a percentage
                answer = droppedusers/numtotalusers
                answer = answer * 100

                print(f"{numtotalusers} users finished or have started watching {jsonr['title']}, and {droppedusers} users dropped it")
                print(jsonr['title'] + " has a drop rate of " + '{:.2f}%'.format(answer))
                print("-----------------------------------------------------------------------------------------------")

            elif dropEvent == 'Sumbit top parameters':
                #Do input checking here later, especially make sure -TOPX- is a number
                #print(f"Picked second option in first screen, input text would be {dropValue['-TOPX-']} with dropdown option of {dropValue['-COMBO-']}, did we check the box: {dropValue['-CHECK-']}")
                #dropped - a list of tuples with drop rate at index 0 and node index at index 1
                dropped = []

                #First, get the top X anime
                url = f"https://api.myanimelist.net/v2/anime/ranking?ranking_type={optionToOption[dropValue['-COMBO-']]}&limit={dropValue['-TOPX-']}"
                headers = {"X-MAL-CLIENT-ID" : os.environ["MALAPIKEY"]}
                response = requests.get(url, headers = headers)
                jsonr = response.json()
                
                #Iterate through the ranking to get drop rate for each anime
                for index, node in enumerate(jsonr['data']):
                    #Need to make one request for every anime in the selected ranking
                    #Make URL by getting the ID from the node and send the request
                    nodeUrl = f"https://api.myanimelist.net/v2/anime/{node['node']['id']}?fields=statistics"
                    nodeResponse = requests.get(nodeUrl, headers = headers)
                    nodeJson = nodeResponse.json()

                    #Get total users and dropped users from the response
                    numtotalusers = int(nodeJson['statistics']['num_list_users']) - int(nodeJson['statistics']['status']['plan_to_watch'])
                    droppedusers = int(nodeJson['statistics']['status']['dropped'])

                    #Calculate answer and convert to a percentage
                    answer = droppedusers/numtotalusers
                    answer = answer * 100
                    #Add to the list of tuples so that it can then be sorted by percentage if required
                    dropped.append((answer, index))
                if(dropValue['-CHECK-']):
                    #Want to sort by drop rate, index 0 in the tuple
                    #Want highest drop rate first
                    dropped.sort(key = lambda item : item[0], reverse = True)

                #List title
                print("-----------------------------------------------------------------------------------------------")
                if not dropValue['-CHECK-']:
                    print(f"Top {dropValue['-TOPX-']} anime ({dropValue['-COMBO-'].lower()} ranking)")
                else:
                    print(f"Top {dropValue['-TOPX-']} anime ({dropValue['-COMBO-'].lower()} ranking) sorted by drop rate")
                print("-----------------------------------------------------------------------------------------------")

                #Iterate again to print
                for num, dropTuple in enumerate(dropped, 1):
                    #Index 1 of the dropTuple is its index in the 'data' list from the ranking response
                    node = jsonr['data'][dropTuple[1]]
                    if(dropValue['-CHECK-']):
                        print(str(num) + ". " + node['node']['title'] + " (ranked " + str(node['ranking']['rank']) + ") has a drop rate of " + '{:.2f}%'.format(dropTuple[0]))
                    else:
                        print(str(num) + ". " + node['node']['title'] + " has a drop rate of " + '{:.2f}%'.format(dropTuple[0]))
                    
                print("")

            elif dropEvent.startswith('Go'):
                windowDrop.close()
                break
            elif dropEvent == "Clear":
                windowDrop['-OUTPUT-'].update('')
        #Original plan was to also be able to return a graph that given a user's list returns time watched per rating,
        #but MAL Graphs can already do that.



