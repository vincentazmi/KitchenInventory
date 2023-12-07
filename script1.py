import pytesseract,os,sys,time,statistics
from datetime import datetime
from PIL import Image, ImageEnhance
from deskew import determine_skew

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
img = input("Enter image directory/name: (or enter for default image 'images/IMG_5670.jpg'")
if img == "":
    img = "images/IMG_5670.jpg"

receiptImage = Image.open(img)

def imageToBG(image, wPercentage):#, bPercentage):
    pixels = image.load()
    width, height = image.size
    # if horizontal: rotate image to portrait 
    if width>height:
        image = image.rotate(270,expand=True)
        pixels = image.load()
        width, height = image.size
    
    # cPercentage = colour percentage of 255
    wMinimum = 255-255*wPercentage # calculated minimum white-ish colour value
##    bMaximum = 255*bPercentage # calculated maximum black-sih colour value
    

    for x in range(width):
        for y in range(height):
            # set pixels above white percentage to green
            

            

            if pixels[x,y][0] > wMinimum and \
               pixels[x,y][1] > wMinimum and \
               pixels[x,y][2] > wMinimum:
                pixels[x,y] = (0,255,0)

##            elif pixels[x,y][0] < bMaximum and \
##                 pixels[x,y][1] < bMaximum and \
##                 pixels[x,y][2] < bMaximum:
##                  pixels[x,y] = (255,0,0)

            # set all others to black
            else:
                pixels[x,y] = (0,0,0)

    image.save("pimages/1blackAndGreen.png")


def findGreenX(image, verticalPercentage):
    pixels = image.load()
    width, height = image.size

    
    """Finding x coordinate of fully green vertical lines"""
    greenX = []
    
    for x in range(width): # for each x value
        greenCount, notGreenCount = 0,0
        for y in range(height): # go all the way down
            if pixels[x,y] == (0,255,0):
                greenCount += 1
            else:
                notGreenCount += 1
                
        if greenCount/(greenCount+notGreenCount) > verticalPercentage:
##            print(x, greenCount,notGreenCount,greenCount/(greenCount+notGreenCount))
            greenX.append((x,greenCount/(greenCount+notGreenCount)))
            for y in range(height):
                if pixels[x,y] == (0,255,0):
                    pixels[x,y] = (0,0,255) # correct line will be blue
                else:
                    pixels[x,y] = (255,0,0) # interferences will be red
        
    image.save("pimages/2greenX.png")
    
    return greenX

def createBlueBorder(image, greenX, edgeDeviation):
    pixels = image.load()
    width, height = image.size

    """Creating blue border"""
    # edgeDeviation is the amount of pixels the border can move left or right
    textProtection = 10 # pixel count between text and receipt edge
    
    leftBorder, rightBorder = [],[]
    prevL = "X"
    prevR = "X"
    
    doLeft, doRight = True,True
    if greenX[0][1] == 1:
##        print("ya")
        x = greenX[0][0]
        for y in range(height):
            
            pixels[x,y] = (0,0,255)
            leftBorder.append(x)
        doLeft = False

    if greenX[-1][1] == 1:
##        print("ya2")
        x = greenX[-1][0]
        for y in range(height):
            pixels[x,y] = (0,0,255)
            rightBorder.append(x)
        doRight = False
    
    for y in range(height):
        if doLeft:
            """Left border"""
            # start from first x where green all the way down
            x = greenX[0][0]
            # travel left until no longer green:
            while pixels[x,y] == (0,255,0):
    ##            pixels[x,y] = (255,0,0)
                x -= 1
            x += 1
            if prevL == "X": prevL = x # first run, define prevL
            
            if x > prevL and x-prevL > textProtection: # if trying to go toward middle too much (deleting text), go from prevL
                x = prevL
                while pixels[x,y] == (0,255,0):
                    x -= 1
                x += 1
        
            # if going out too much, take previous edge
            if x < prevL and prevL-x > edgeDeviation:
                x = prevL
            
            # set border to blue
            pixels[x,y] = (0,0,255)
            leftBorder.append(x)
            prevL = x
        
        if doRight:
            """Right border"""
            # start from last x where green all the way down
            x = greenX[-1]
            # travel right until no longer green:
            while pixels[x,y] == (0,255,0):
    ##            pixels[x,y] = (255,0,0)
                x += 1
            x -= 1
            if prevR == "X": prevR = x

            if x < prevR and prevR-x > textProtection: # if trying to go toward middle too much (deleting text), go from prevR
                x = prevR
                while pixels[x,y] == (0,255,0):
                    x += 1
                x -= 1
                
            # if going out too much, take previous edge
            if x > prevR and x-prevR > edgeDeviation:
                x = prevR
            
            # set border to blue
            pixels[x,y] = (0,0,255)
            rightBorder.append(x)
            prevR = x

    image.save("pimages/3blueBorder.png")
    return leftBorder, rightBorder

def filterOriginal(original, image, leftBorder, rightBorder):
    pixels = image.load()
    width, height = image.size

    borders = {}

    for x in range(width):
        for y in range(height):
            if pixels[x,y] == (0,0,255):
                if x > width/2: # right side of receipt
                    borders[y].append(x)
                else: # left side of receipt
                    borders[y] = [x]

    pixels = original.load()
    width, height = original.size
    if width>height:
        original = original.rotate(270,expand=True)
        pixels = original.load()
        width, height = original.size

    for y,xs in borders.items():
        # from x=0 to left border:
        for x in range(0,xs[0]):
            pixels[x,y] = (0,0,0)
        # keep border
        pixels[xs[0],y] = (0,0,255)
        # from right border to right edge:
        for x in range(xs[1],width):
            pixels[x,y] = (0,0,0)
        # keep border
        pixels[xs[1],y] = (0,0,255)

    
    
    original.save("pimages/4removedBackground.png")

def bWImage(image, wPercentage):
    pixels = image.load()
    width, height = image.size

    wMinimum = 255-255*wPercentage # calculated minimum white-ish colour value

    for x in range(width):
        for y in range(height):
            if pixels[x,y][0] > wMinimum and \
               pixels[x,y][1] > wMinimum and \
               pixels[x,y][2] > wMinimum:
                pixels[x,y] = (255,255,255)

            # if not border or above is true, set pixel to black
            elif pixels[x,y] != (0,0,255):
                pixels[x,y] = (0,0,0)

    image.save("pimages/5bWImage.png")

def borderLines(image):
    pixels = image.load()
    width, height = image.size

    # list of all y coordinates that are fully white across the receipt
    blueL = "X"
    blueY = []

    yFromTo = []
    consecutiveCount = 0
    for y in range(height):
        white = False
        for x in range(width):
            # after first border crossed, check for black pixels
            if white:
##                print(x)
                # if second border found without meeting fail condition
                if pixels[x,y] == (0,0,255):
                    for bx in range(blueL,x):
                        pixels[bx,y] = (0,0,255)
                    try:
                        if yFromTo[-1] != y-consecutiveCount:
                            yFromTo.append(y)
                    except IndexError:
                        yFromTo.append(y)
                    consecutiveCount += 1
                    break

                # fail condition: if met go to next y
                if pixels[x,y] == (0,0,0):
##                    print("break")
                    if consecutiveCount != 0:
                        yFromTo.append(y-1)
                        consecutiveCount = 0
                    break
##                pixels[x,y] = (0,0,255)
                    
            # if blue border found
            if pixels[x,y] == (0,0,255):
                blueL = x
                white = True
##        print(y)

    image.save("pimages/6yGapLines.png")

def findItemsYGap(image, leftBorder, gapDeviation):
    pixels = image.load()
    width, height = image.size

    gaps = []
    count = 0
    for y in range(height):
        x = leftBorder[y]+1
        if pixels[x,y] == (0,0,255):
            if count>0: gaps.append(count)
            count = 0
        else: count += 1

    mode = statistics.mode(gaps)
    myMin = mode-gapDeviation
    myMax = mode+gapDeviation
    
##    print(mode)
##    print(gaps)
##    [print(i) for i in gaps if i>=myMin and i<=myMax]

    
    count = 0
    inGap = False
    for y in range(height):
        x = leftBorder[y]+1
        if pixels[x,y] != (0,0,255):
            inGap = True
            try:
                gap = gaps[count]
            except IndexError: pass#print(x,y,count,len(gaps))
            if gap < myMin or gap > myMax:
                while pixels[x,y] != (0,0,255):
                    pixels[x,y] = (0,0,255)
                    x += 1
                    
        else:
            if inGap:
##                print(count,gaps[count])
                count += 1
                inGap = False



                    

    image.save("pimages/7averageGaps.png")


def splitLines(image, cropImage, leftBorder, rightBorder):
    pixels = image.load()
    width, height = image.size

    count = 0
    getBottom = False
    for y in range(height):
        x = leftBorder[y]+1
        if pixels[x,y] != (0,0,255):
            if not getBottom:
                top = y
                getBottom = True
                
        if getBottom and pixels[x,y] == (0,0,255):
            left = x
            right = rightBorder[y]-1
            bottom = y
            pad = 1
##            print(count,left,top,right,bottom)
            img = cropImage.crop((left,top-pad,right,bottom+pad))
            img.save("lines/{}.png".format(count))
            getBottom = False
            count += 1
                
        
def readLines():
##    config = '--oem 3 --psm 6'
##    for i in range(6,14):
##        config = '--oem 3 --psm %d' % i
##        print(i)
##        print(pytesseract.image_to_string(Image.open("lines/3.png"), config=config, lang='eng'))
    config = '--oem 3 --psm 10'# % i
    for i in range(95):
        img = Image.open("lines/{}_2.png".format(i))
        print(pytesseract.image_to_string(img, config=config, lang='eng'))
##        new_size = tuple(4*x for x in img.size)
##        img = img.resize(new_size, Image.LANCZOS)
##        img.save("lines/{}_2.png".format(i))
        img.close()

##    config = '--oem 3 --psm 10'# % i
##    import numpy as np
##    from skimage import io
##    from skimage.color import rgb2gray
##    from skimage.transform import rotate
##
##    from deskew import determine_skew
##
##    
##    image = io.imread('lines/0_2.png')
##    grayscale = rgb2gray(image)
##    angle = determine_skew(grayscale)
##    print(angle)
##    rotated = rotate(image, angle, resize=True) * 255
##    io.imsave('output.png', rotated.astype(np.uint8))
##    print(pytesseract.image_to_string(Image.open("lines/5_2.png"), config=config, lang='eng'))
##    img = Image.open('pimages/7averageGaps.png')
##    angle = determine_skew(img)
##    img = img.rotate(angle)
##    img.show()
    
    
##    for i in range(95):
##        print(pytesseract.image_to_string(Image.open("lines/{}_2.png".format(i)), config=config, lang='eng'))
    


##img = ImageEnhance.Contrast(receiptImage).enhance(10)
##width, height = img.size
##if width>height: img = img.rotate(270,expand=True)
##img.save("pimages/0contrast.png")

"""STEP 1"""
# Filters filters white-ish and black-ish to fully white and black by given colour percentage
##imageToBG(Image.open("pimages/0contrast.png"), wPercentage=0.40)#, bPercentage=0.30)

"""Step 2"""
##greenX = findGreenX(Image.open("pimages/1blackAndGreen.png"), verticalPercentage=0.999)

"""STEP 3"""
# Creates blue border around the edge with given pixel variation amount (+-x value from above edge x coordinate)
##leftBorder, rightBorder = createBlueBorder(Image.open("pimages/1blackAndGreen.png"), greenX, edgeDeviation=2)

"""STEP 4"""
# Removes background from original image according to blue border created in step 2
##filterOriginal(receiptImage, Image.open("pimages/3blueBorder.png"), leftBorder, rightBorder)

"""Step 5"""
##bWImage(Image.open("pimages/4removedBackground.png"),0.45)

"""Step 6"""
##borderLines(Image.open("pimages/5bWImage.png"))

"""Step 7"""
##findItemsYGap(Image.open("pimages/6yGapLines.png"), leftBorder, gapDeviation=12)

"""Step 8"""
##splitLines(Image.open("pimages/7averageGaps.png"), Image.open("pimages/5bWImage.png"), leftBorder, rightBorder)

"""Step 9"""
readLines()



if __name__ == "__main__": pass
