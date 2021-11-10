
import re

# Input text testimmony file (list of strings)
# Picks out the participant names and prints them back out to replace duplicate entries
def printParticipants(fullText):
    lines = fullText.split('\n')
    participants = []
    timestamp_str1 = '\(\d\d:\d\d\)'
    timestamp_str2= '\(\d\d:\d\d:\d\d\)'
    for line in lines:
        # Do we have either timestamp formats used? Indicates a new speaker
        match1 = bool(re.search(timestamp_str1, line))
        match2 = bool(re.search(timestamp_str2, line))

        if match1 or match2:
            speaker = "'" + line.split(':')[0] + "'"
            if speaker not in participants:
                participants += [speaker]

    participants.sort()
    print('\n'.join(participants))

# Loop through lines and replace pairs of names that are actually the same
def replacePairs(fullText, pairs):
    for toReplace, replaceWith in pairs:
        fullText = fullText.replace(toReplace, replaceWith)
    return fullText

fileName = 'COVID Senate Testimony'
f = open(fileName + '.txt', 'r', encoding = 'utf-8')
rawText = f.read().strip()
f.close()

# CLEANING THE FILE
# printParticipants(rawText)
pairs = [['Sen.', 'Senator']]\
    # , ['Mr.', 'Senator'],
    #      ['Chairman', 'Senator'],
    #      ['Harry Dunn', 'Speaker Harry Dunn'],
    #      ['Marsha Blackburn', 'Senator Blackburn'],
    #      ['Jon Ossoff', 'Senator Ossoff']]


cleanedText = replacePairs(rawText, pairs)
printParticipants(cleanedText)
f = open(fileName + '_Clean.txt', 'w')
f.write(cleanedText)
f.close()



