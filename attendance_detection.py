
import cv2
from tqdm import tqdm
import numpy as np

IMAGE = "warped_thresh.jpg"
MOVE_DOWN = 3

image = cv2.imread(IMAGE)
image = cv2.resize(image, (image.shape[1]//3, image.shape[0]//3))
orig = image.copy()
orig2 = image.copy()
image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
def get_vert_line(img):
    shape = img.shape
    idxs = []
    for x in range(shape[0]):
        idx = 0
        for y in range(shape[1]):
            if img[x][y] < 100:
                idx = y
                break
        idxs.append(idx)
    return idxs

def get_horizontal_lines(img, idxs, skip_top_pixels=40, horizontal_check=7, threshold=150):
    lines = []
    shape = img.shape

    for i, idx in enumerate(idxs):
        if i < skip_top_pixels:
            continue
        else:
            startpoint = [idx,i]
            current_point = [i, idx]
            while True:
                pixels = []
                temp_dict = {}
                if (current_point[0]+3 >= shape[0] or current_point[1]+3 >= shape[1]):
                    #print(f"current_point[0]+3 >= shape[1] : {current_point[0]+3 >= shape[1]}")
                    #print(f"current_point[1]+3 >= shape[0] : {current_point[1]+3 >= shape[0]}")
                    #print(f"Current:{current_point}, Shape:{shape}")
                    endpoint = [current_point[1], current_point[0]]
                    break

                for px in range(1,horizontal_check+1):
                    # TODO Change (In case of multiple points having same pixel value)
                    temp_dict[img[current_point[0]-1][current_point[1]+px]] = f"{current_point[0]-1},{current_point[1]+px}"
                    temp_dict[img[current_point[0]+1][current_point[1]+px]] = f"{current_point[0]+1},{current_point[1]+px}"
                    temp_dict[img[current_point[0]][current_point[1]+px]] = f"{current_point[0]},{current_point[1]+px}"


                for px in temp_dict.keys():
                    pixels.append(px)
                #print(f"current_pt {current_point}, Dict:{temp_dict.values()} : {pixels}")
                if (min(pixels) > threshold):
                    endpoint = [current_point[1], current_point[0]]
                    break
                else:
                    idxz = temp_dict[min(pixels)].split(",")
                    current_point = (int(idxz[0]), int(idxz[1]))
            lines.append([startpoint, endpoint])
    return lines




def trim_lines(lines):
    rem = []
    for x in lines:
        if (x[1][0] - x[0][0]) < 70:
            rem.append(x)

    for x in rem:
        lines.remove(x)
    cv2.drawContours(orig2, np.array(lines), -1, (255, 255, 255), 2)
    cv2.imwrite("Img_for_checking.jpg", orig2)
    return lines


def get_final_lines(lines):
    new_lines = []
    temp = []
    for x in lines:
        if x[1] != temp:
            new_lines.append(x)
            temp = x[1]
        else:
            continue
    for x in range(len(new_lines)):
        new_lines[x][0][1] += MOVE_DOWN

    return new_lines



def get_first_att_line(lines, img_shape, percentage=60):
    line_idx = 0
    thresh = (percentage * img_shape[1]) / 100
    for i, line in enumerate(lines):
        if line[1][0]-line[0][0] >= thresh:
            line_idx = i+1
            break
    return line_idx


def is_below(slope, const, pt):
    if pt[1] > (slope * pt[0] + const):
        return True
    else:
        return False


def get_line_equation(pta, ptb):
    m = (ptb[1]-pta[1])/(ptb[0]-pta[0])
    c = pta[1] - m * pta[0]
    return m,c


print(image.shape)
idxa = get_vert_line(image)
lines = get_horizontal_lines(image, idxa)
lines = trim_lines(lines)
new_lines = get_final_lines(lines)

first_line_idx = get_first_att_line(new_lines, image.shape, 60)
attendance = []
for line_idx in range(first_line_idx, len(new_lines)-1):
    l1 = new_lines[line_idx]
    l2 = new_lines[line_idx+1]
    slope1, const1 = get_line_equation(l1[0], l1[1])
    slope2, const2 = get_line_equation(l2[0], l2[1])
    thresh = 150
    pixels = []
    #print(min(l1[0][1], l1[1][1]), max(l2[0][1], l2[1][1]))
    #print(l1[0][0], image.shape[1]//2)
    for x in range(min(l1[0][1], l1[1][1]), max(l2[0][1], l2[1][1])):
        for y in range(l1[0][0], image.shape[1]//2):
            if(is_below(slope1, const1, [y,x]) and not is_below(slope2, const2, [y,x])):
                pixels.append(image[x][y])


    count = 0
    for x in pixels:
        if x < thresh:
            count+=1

    if count > 1000:
        attendance.append(f"{line_idx-first_line_idx+1}, P")
    else:
        attendance.append(f"{line_idx-first_line_idx+1}, A")

print(attendance)
