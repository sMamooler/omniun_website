def getAbridgedSettings(gcodeText, abridgedSettings, lines, archive, getTextLines, settingsStart=False):
    for line in lines:
        splitLine = gcodec.getSplitLineBeforeBracketSemicolon(line)
        firstWord = gcodec.getFirstWord(splitLine)
        if firstWord == '<setting>' and settingsStart:
            if len(splitLine) > 4:
                abridgedSettings.append(AbridgedSetting(splitLine))
        elif firstWord == '<settings>':
            settingsStart = True
        elif firstWord == '</settings>':
            return abridgedSettings
    return []
