import cv2 as cv

picture = cv.imread('pic.jpeg')

if picture is None:
    print("Error, the picture was not able to load properly")

else:
    grayscale_picture = cv.cvtColor(picture, cv.COLOR_BGR2GRAY)
    cv.imwrite("gray_picture.jpeg", grayscale_picture)
    
    # 1. FIX: Convert the 1-channel gray image to a 3-channel gray image
    grayscale_3channel = cv.cvtColor(grayscale_picture, cv.COLOR_GRAY2BGR)
    
    # 2. FIX: Use the 3-channel gray image in the concatenation list
    pic = cv.hconcat([picture, grayscale_3channel])
    
    cv.imshow("Side-by-Side Comparison", pic)
    cv.waitKey(0)
    cv.destroyAllWindows()
