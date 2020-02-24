import cv2
import numpy as np
import matplotlib.pyplot as plt
import imutils
from skimage.filters import threshold_local
from tqdm import tqdm



def invert(data_elem, threshold=100):
    """
    threshold reduce whitens the image
    """
    shape = data_elem.shape
    return np.array([255 if y > threshold else y for x in data_elem for y in x], dtype="uint8").reshape(shape)



def horizontal_line_idxr(image, threshold=160):
    new_img = list(image.copy())
    idxlst = []
    for row, x in enumerate(new_img):
        flag = True
        #print(f"Row: {row}")
        for idx, y in enumerate(x):
            #x[idx] = 0
            if y < threshold:
                idxlst.append(f"{row},{idx}")
                flag = False
                break
        if flag:
            idxlst.append(f"{row},{len(x)}")
    del new_img
    return idxlst



def horizontal_processing(image, idxs, offset=0, img_pct_threshold=60):
    """
    img_pct_threshold: Draw line if the line's length will be at least 60%(default) of the image
    offset: No of pixels to stop short of detected obstacles
    idxs: contains the row no and length of line [row,length]
    """
    new_img = list(image.copy())
    for i, idx in enumerate(idxs):
        tmp = idx.split(",")
        darken_range = 0
        if int(tmp[1]) > (len(image[0]) - (10*len(image[0]))//100):
            darken_range = len(image[1])
        else:
            darken_range = int(tmp[1])-offset

        if darken_range > (len(image[0]) - ((100-img_pct_threshold)*len(image[0]))//100):
            for pixel in range(darken_range):
                new_img[int(tmp[0])][pixel] = 0
    return np.array(new_img, dtype='uint8')



def vertical_line_idxr(image, pixel_move=19, threshold=160):
    #
    horizontal_mov_flag = False
    pxmv = pixel_move
    idxs = []
    for i in range(len(image[0])):
        flag = True
        if horizontal_mov_flag:
            pxmv -= 1
            if pxmv > 0:
                continue
            else:
                horizontal_mov_flag = False
                pxmv = pixel_move
        else:
            for j in range(len(image)):
                if image[j][i] < threshold and image[j][i] > 1:
                    if pixel_move > 5:
                        horizontal_mov_flag = True
                    idxs.append(f"{i},{j}")
                    flag=False
                    break
            if flag:
                idxs.append(f"{i},{image.shape[0]}")

    return idxs


def vertical_processing(image, idxs, offset=0, img_pct_threshold=60):
    """
    img_pct_threshold: Draw line if the line's length will be at least 60%(default) of the image
    offset: No of pixels to stop short of detected obstacles
    idxs: contains the row no and length of line [column,length]
    """
    new_img = list(image.copy())
    for i, idx in enumerate(idxs):
        tmp = idx.split(",")
        if int(tmp[1]) > (len(image) - ((100-img_pct_threshold)*len(image))//100):
            for y in range(int(tmp[1]) - offset):
                new_img[y][int(tmp[0])] = 0

    return np.array(new_img, dtype="uint8")


def postprocess(image, left=10, right=10, top=10, bottom=10):
    new_img = list(image.copy())
    for x in range(image.shape[0]):
        for y in range(left):
            new_img[x][y] = 0

    for x in range(image.shape[1]):
        for y in range(top):
            new_img[y][x] = 0

    for x in range(image.shape[1]):
        for y in range(image.shape[0]-bottom, image.shape[0]):
            new_img[y][x] = 0

    for x in range(image.shape[0]):
        for y in range(image.shape[1]-right, image.shape[1]):
            new_img[x][y] = 0

    return np.array(new_img, dtype="uint8")


IMAGE = "blank.jpg"
DRAWING_INV_THRESH = 140    # Default = 140
USEFUL_INV_THRESH = 160     # Default = 160

POST_LEFT = 30
POST_BOTT = 0
POST_TOP = 40
POST_RIGHT = 0

VERT_LINE_PCT = 80          # Default = 80
HOR_LINE_PCT = 80           # Default = 80

#Pixels less than this are detected as obstacles
THRESHOLD_VERT = 160        # Default = 160
THRESHOLD_HOR = 160         # Default = 160


VERT_PIXEL_MOVE = 40      # Default = 19

img = cv2.imread(IMAGE)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
gray = cv2.resize(gray, (gray.shape[0]//3, gray.shape[1]//4))

gray_drawing = invert(gray, threshold=DRAWING_INV_THRESH)
gray_useful = invert(gray, threshold=USEFUL_INV_THRESH)

cv2.imshow("Drawing", gray_drawing)
cv2.imshow("Useful", gray_useful)
cv2.waitKey(0)
cv2.destroyAllWindows()

drawing_image = threshold_local(gray_drawing, 5, offset = 10, method = "gaussian")
drawing_image = drawing_image.astype(np.uint8, copy=False)
useful_image = threshold_local(gray_useful, 3, offset = 10, method = "gaussian")
useful_image = useful_image.astype(np.uint8, copy=False)
cv2.imshow("Drawing", drawing_image)
cv2.imshow("Useful", useful_image)
cv2.waitKey(0)
cv2.destroyAllWindows()

idxs = horizontal_line_idxr(drawing_image, threshold=160)
useful_image = horizontal_processing(image=useful_image, idxs=idxs, offset=30, img_pct_threshold=HOR_LINE_PCT)

cv2.imshow("Outline", useful_image)
cv2.waitKey(0)
cv2.destroyAllWindows()

idxs = vertical_line_idxr(drawing_image, threshold=160, pixel_move=VERT_PIXEL_MOVE)
final = vertical_processing(useful_image, idxs, offset=20, img_pct_threshold=VERT_LINE_PCT)
final = postprocess(final, left=POST_LEFT, bottom=POST_BOTT, top=POST_TOP, right=POST_RIGHT)

cv2.imshow("Outline", final)
cv2.waitKey(0)
cv2.destroyAllWindows()
cv2.imwrite(IMAGE.split(".")[0]+"_generic.jpg", final)

