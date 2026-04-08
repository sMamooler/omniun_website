def getLoopsInOrderOfArea(compareAreaFunction, loops, loopAreas=[]):
    for loop in loops:
        loopArea = LoopArea(loop)
        loopAreas.append(loopArea)
    loopAreas.sort(compareAreaFunction)
    loopsInDescendingOrderOfArea = []
    for loopArea in loopAreas:
        loopsInDescendingOrderOfArea.append(loopArea)
    return loopsInDescendingOrderOfArea
