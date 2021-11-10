# ********************************************************* #
#
#               Senate Testimony Stats
#
# ********************************************************* #
# Last Updated:
#   10/30/2021 -    Created script. Added cleaning fns.
#   10/31/2021 -    Added sorting of exchanges. Revised Participant & Exchange object parameters
#   11/06/2021 -    Added openTime to set start of openings when no swearing in.
#                   Changed skip if statement for new exchanges to always include satements
#                   from the chair saying "recess".
#   11/08/2021 -    Changed skip statement to only exclude senator name calls that are under 150 chars.
#                   Added parseTime() fn
#                   Made any long breaks ensure new exchange created
#                   Took out restriction for chairman empty exchanges getting added to MSC time col.
#                   Added ability to have more than 1 testifier
#
# For next time:
# Need to fix recess check. It's adding ~1/2 hr to bloomenthals time
#


class Exchange():
    questioner = None              # The senator asking questions in this exchange

    def __init__(self, senatorName, startTime):
        self.startTime = startTime
        self.questioner = Participant(senatorName)
        self.answerer = None
        self.length = 0                 # Number of minutes in the exchange
        self.lengthStr = ''

    def setAnswerer(self, name):
        self.answerer = Participant(name)

    def addText(self, participant, time, text):
        if participant == self.questioner.name:
            self.questioner.addText(time, text)
        else:
            if self.answerer is None:
                self.setAnswerer(participant)
            self.answerer.addText(time, text)

    def setLength(self, startTime, endTime):
        date_start = parseTime(startTime)
        date_end = parseTime(endTime)
        difference = date_end - date_start

        self.lengthStr = '%02d' %int(difference.seconds/60) + ':' + '%02d' %(difference.seconds%60)
        self.length = float(difference.seconds)/60.0

    def getTotals(self):
        print('Write this part')

class Participant():

    def __init__(self, name):
        self.name = name
        self.words = 0
        self.questions = 0
        self.statements = 0
        self.times = {}

    def addText(self, time, text):
        text = text.replace('...', '.') + '\n'
        self.words += text.count(' ') + 1
        self.statements += text.count('.')
        self.questions += text.count('?')
        self.times[time] = text

# Input timestamp from testimony files.
# Return datatime object
def parseTime(timeStr):
    timestamp_str1 = '\(\d\d:\d\d\)'
    timestamp_str2 = '\(\d\d:\d\d:\d\d\)'
    match1 = bool(re.search(timestamp_str1, timeStr))
    match2 = bool(re.search(timestamp_str2, timeStr))
    toParse = timeStr.replace(')', '').replace('(', '')

    if match1:
        minutes, seconds = toParse.split(':')
        hours = 0
    else:
        if not match2:
            print('no match?', timeStr)
        hours, minutes, seconds = toParse.split(':')

    return datetime(year = 2021, month = 1, day = 1, hour = int(hours), minute = int(minutes), second = int(seconds))


# Writes the data to a new excel file
#   datasets: lists of rows to write [[headers], [row0], [row1]]
#   fileName: string name of file. Needs .xlsx
#   sheetNames: list of strings to use as sheet tab labels
def writeExcel(datasets, filePath, sheetNames = []):
    wb = workbook.Workbook(filePath, {'strings_to_numbers' : True})

    for a, name in enumerate(sheetNames):
        newSheet = wb.add_worksheet(name)
        thisData = datasets[a]
        for i, row in enumerate(thisData):
            newSheet.write_row(i, 0, list(row))

    wb.close()


import re
from datetime import datetime
from datetime import time
from datetime import timedelta
from xlsxwriter import workbook

# TESTIMONY SPECIFIC VARIABLES
# chairman = 'Senator Blumenthal'                                     # id of chair to recognize opening & closing exchange
# min_chairman = 'Senator Blackburn'                                  # id of minority chairman to recognize opening
# testifying = ['Frances Haugen']                                     # List of testifier IDs
# openTime = '(26:44)'                                                # Timestamp of opening statement (only used if testifier not sworn in)
# fileName = 'Facebook W Senate Testimony_Clean.txt'                  # use cleanFile.py to get cleaned version of file
# finalfileName = 'Oct 5th - Facebook W Senate Testimony Metrics.xlsx'

# chairman = 'Senator Durbin'                  # id of chair to recognize opening & closing exchange
# min_chairman = 'Senator Grassley'  #            # id of minority chairman to recognize opening
# testifying = ['AG Garland'] #                                    # List of testifier IDs
# openTime = ''
# fileName = 'AG Senate J Testimony_Clean.txt'
# finalfileName = 'Oct 27 - AG Senate J Testimony Metrics.xlsx'

# chairman = 'Senator Durbin'                  # id of chair to recognize opening & closing exchange
# min_chairman = 'Senator Grassley'  #            # id of minority chairman to recognize opening
# testifying = ['Hon. Christoper A. Wray'] #                                    # List of testifier IDs
# openTime = ''
# fileName = 'FBI Senate J Testimony_Clean.txt'
# finalfileName = 'Mar 2 - FBI Senate J Testimony Metrics.xlsx'

chairman = 'Senator Murray'                  # id of chair to recognize opening & closing exchange
min_chairman = 'Senator Burr'  #            # id of minority chairman to recognize opening
testifying = ['Dr. Fauci',
                'Dr. Walensky',
                'Dr. Woodcock',
                'Ms. O’Connell'] #                                    # List of testifier IDs
openTimes = ['(18:11)', '(23:31)', '(28:58)', '(34:24)']
fileName = 'COVID Senate Testimony_Clean.txt'
finalfileName = 'Nov 4 - COVID Senate Testimony Metrics.xlsx'

# Read in the file!
f = open(fileName, 'r')
rawText = f.read().strip()
f.close()
lines = rawText.split('\n')


# *******************************#
# Sorting lines into linesLabeled
# Groups lines that are part of 1 chunk together with 1 start time
# Pairs speaker & time with actual text
linesLabeled = []       # [[speaker (str), time (str), text (str)], [speaker, time, text]]
senators = []           # Names of all senators

# Strings to be matched when checking timestamps
timestamp_str1 = '\(\d\d:\d\d\)'
timestamp_str2= '\(\d\d:\d\d:\d\d\)'
# Variables to be redefined in each loop
lastSpeaker = None
lastTime = '(00:00)'
lastTime_date = None
timeDiff = 0                                # The number of minutes between statements for finding recess or breaks in hearing

text = ''
for line in lines:
    if len(line.strip()):
        # Do we have either timestamp formats used? Indicates a new speaker
        match1 = bool(re.search(timestamp_str1, line))
        match2 = bool(re.search(timestamp_str2, line))
        if match1 or match2:                    # Found a timestamp
            speaker, thisTime = line.split(': ')    # The speaker just found
            thisTime_date = parseTime(thisTime)

            if lastTime_date is not None:
                timeDiff = (thisTime_date - lastTime_date).seconds/60

            # New speaker different than who was just speaking
            # or just back from recess
            if speaker != lastSpeaker or timeDiff > 15:
                if lastSpeaker is not None:     # Not the first speaker
                    # Add the last speakers name, first timestamp and text to linesLabeled
                    linesLabeled += [[lastSpeaker, lastTime, text]]
                    text = ''

                # If this is a video or display we don't need to add it to lines for sorting
                if speaker.find('Speaker') > -1:
                    lastSpeaker = None
                else:
                    lastSpeaker = speaker
                    # If we found one of the senators
                    if speaker not in testifying and speaker not in senators and speaker.find('Speaker') == -1:
                        senators += [speaker]

                # Set values of last values to this speaker & time
                lastTime = thisTime
                lastTime_date = thisTime_date

        else:
            if len(text):
                text += ' '     # space between lines
            text += line

# *******************************#
# Sorting linesLabeled into list of exchange objects
# Exchanges define questoner & answerer (Participant objects)
# as well as numbers of questions, statements & length.
# Also (tries) to find opening statements from chair & minority chair
exchanges = []                              # List of exchange objs in order
start = False                               # Will start once 'I do.' is found in file
lastSpeaker = None                          # The last person to ask questions
chair_opening = ''
min_opening = ''
testifier_openings = dict.fromkeys(testifying, '')
closing = ''
for z, line in enumerate(linesLabeled):
    speaker, thisTime, text = line
    thisTime_date = parseTime(thisTime)
    if lastTime_date is not None:
        timeDiff = (thisTime_date - lastTime_date).seconds/60

    if start:

        # Skips exchanges:
        #   chairman just calling on the next speaker
        #   exchanges shorter than 150 characters
        # Never skips exchanges containing the word recess
        containsSenator = bool(sum([int(text.find(s) > -1) for s in senators]))
        textLen = len(text)
        if not ((speaker == chairman and containsSenator and len(text) < 100) and text.lower().find('recess') == -1):
        #if not (len(text) < 150 and text.lower().find('recess') == -1):

            # If we found a senator asking questions, and it's a different senator than before
            # or it's a new exchange after a break in the hearing
            # create new exchange
            if speaker not in testifying and (speaker != lastSpeaker or timeDiff > 15):
                exchange = Exchange(speaker, thisTime)
                exchanges += [exchange]

            # Add to opening statement of testifier
            # Can span multiple exchange lines if "I do" is included with chairman interruption in between
            if speaker in testifying and len(testifier_openings[speaker]) < 15:
                testifier_openings[speaker] += text
                #del exchanges[0]
                #lastSpeaker = None

            else:
                # If we found a different testifier than in the current exchange
                # create new exchange and add last question to this exchange
                if speaker != lastSpeaker and exchange.answerer != None and speaker != exchange.answerer.name:
                    lastTime = list(exchange.questioner.times.keys())[-1]
                    lastQ = exchange.questioner.times.pop(lastTime)
                    exchange = Exchange(lastSpeaker, lastTime)
                    exchanges += [exchange]
                    exchange.addText(lastSpeaker, lastTime, lastQ)

                exchange.addText(speaker, thisTime, text)

            if speaker not in testifying:
                lastSpeaker = speaker

            lastTime_date = thisTime_date

    # We haven't hit start yet, add to opening statements
    else:
        # If we hit the swearing in statement
        if text.find('so help you God') > -1:
            start = True
        elif thisTime in openTimes:
            openTimes.remove(thisTime)
            if not len(openTimes):
                # if we found all of the opening statements
                start = True

        if speaker == chairman:
            chair_opening += text + '\n'

        elif speaker == min_chairman:
            if not len(min_opening):
                openingTime = thisTime
            min_opening += text + '\n'

        elif speaker in testifying:
            testifier_openings[speaker] += text + '\n'



# *******************************#
# Set length of time of each exchange
#
lastExchange = None
isRecess = False
for exchange in exchanges:
    if lastExchange is not None:
        # Exchange of chairman just calling recess.
        # Will make lastExchange length = 0 instead of length of recess
        isRecess = bool(sum([int(i.lower().find('recess') > -1) for i in list(lastExchange.questioner.times.values())]))

        if not isRecess:
            # Use this exchange's start time to set the end time of the last exchange in the list
            lastExchange.setLength(lastExchange.startTime, exchange.startTime)

    lastExchange = exchange

# ******************************************#
# Print Statements of Exchange values for QA!
#
# for a, exchange in enumerate(exchanges):
#     print('Exchange', a, 'Length ->', exchange.lengthStr)
#     print(exchange.questioner.name, 'Qs:', exchange.questioner.questions, 'Ss:', exchange.questioner.statements)
#     if exchange.answerer is not None:
#         print(exchange.answerer.name, 'Qs:', exchange.answerer.questions, 'Ss:', exchange.answerer.statements)
#     else:
#         print('No testimony from participant')
#         print(exchange.questioner.times)


# ******************************************#
#           Sorting Exchanges
# Dictionary with key as Senator name.
# Values list of exchange objects where
# that senator was questioner.
#
senatorExchanges = {}
for senator in senators:
    senatorExchanges[senator] = []
    for exchange in exchanges:
        if exchange.questioner.name == senator:
            senatorExchanges[senator] += [exchange]

# ******************************************#
#           Calculating Values
# Create 2 datasets of metrics (see headers):
#   1 per senator & 1 per exchange
#
headers_senators = ['Senator', 'Total Time (min)', 'Time Interacting w/ Testifiers (min)', 'MSC Time (min)',
           'Questions Asked', 'Statements made to Testifiers', 'MSC Statements Made',
           'Questions Illicited from Testifiers', 'Statements Illicited from Testifiers',
           'Word Count Senator', 'Word Count Testifiers', '<- Ratio']
headers_exchange = ['Senator', 'Testifier Name', 'Total Time (min)',
           'Questions Asked', 'Statements made to Testifiers',
           'Questions Illicited from Testifier', 'Statements Illicited from Testifier',
           'Word Count Senator', 'Word Count Testifier', '<- Ratio']

senatorRows = []
exchangeRows = []
for senator in senators:
    thisSenatorRow = [senator] + [0]*(len(headers_senators) - 1)
    thisExchanges = senatorExchanges[senator]
    for exchange in thisExchanges:
        if exchange.answerer != None:
            thisExchangeRow = [senator, exchange.answerer.name] + [0] * (len(headers_exchange) -2)
            thisExchangeRow[headers_exchange.index('Total Time (min)')] += exchange.length
            thisExchangeRow[headers_exchange.index('Questions Asked')] += exchange.questioner.questions
            thisExchangeRow[headers_exchange.index('Statements made to Testifiers')] += exchange.questioner.statements
            thisExchangeRow[headers_exchange.index('Questions Illicited from Testifier')] += exchange.answerer.questions
            thisExchangeRow[headers_exchange.index('Statements Illicited from Testifier')] += exchange.answerer.statements
            thisExchangeRow[headers_exchange.index('Word Count Senator')] += exchange.questioner.words
            thisExchangeRow[headers_exchange.index('Word Count Testifier')] += exchange.answerer.words
            thisExchangeRow[headers_exchange.index('<- Ratio')] += float(exchange.questioner.words/exchange.answerer.words)
            exchangeRows += [thisExchangeRow]

            thisSenatorRow[headers_senators.index('Time Interacting w/ Testifiers (min)')] += exchange.length
            thisSenatorRow[headers_senators.index('Questions Asked')] += exchange.questioner.questions
            thisSenatorRow[headers_senators.index('Statements made to Testifiers')] += exchange.questioner.statements
            thisSenatorRow[headers_senators.index('Questions Illicited from Testifiers')] += exchange.answerer.questions
            thisSenatorRow[headers_senators.index('Statements Illicited from Testifiers')] += exchange.answerer.statements
            thisSenatorRow[headers_senators.index('Word Count Senator')] += exchange.questioner.words
            thisSenatorRow[headers_senators.index('Word Count Testifiers')] += exchange.answerer.words
        else: #if senator != chairman:
            # Banter with chairman/admitting docs
            thisSenatorRow[headers_senators.index('MSC Time (min)')] += exchange.length
            thisSenatorRow[headers_senators.index('MSC Statements Made')] += exchange.questioner.questions
            thisSenatorRow[headers_senators.index('MSC Statements Made')] += exchange.questioner.statements


        thisSenatorRow[headers_senators.index('Total Time (min)')] += exchange.length

    # Find the word count for all of the senators exchanges
    finalSenatorWords = thisSenatorRow[headers_senators.index('Word Count Senator')]
    finalTestifiersWords = thisSenatorRow[headers_senators.index('Word Count Testifiers')]
    if finalTestifiersWords:
        thisSenatorRow[headers_senators.index('<- Ratio')] = float(finalSenatorWords/finalTestifiersWords)

    senatorRows += [thisSenatorRow]

senatorSet = [headers_senators] + senatorRows
exchangeSet = [headers_exchange] + exchangeRows

# ******************************************#
#               Writing File
#
openingSet = [[chairman, chair_opening], ['***', '***', '***'],
            [min_chairman, min_opening], ['***', '***', '***']]
for a, testifier in enumerate(testifying):
    openingSet += [[testifier, '', testifier_openings[testifier]]]
    openingSet += [['***', '***', '***']]
sheetNames = ['By Senator', 'By Exchange', 'Opening Statements']
writeExcel([senatorSet, exchangeSet, openingSet], finalfileName, sheetNames)
