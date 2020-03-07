import argparse
import cv2
from tqdm import tqdm
import numpy as np

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




def trim_lines(lines, orig2):
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
    MOVE_DOWN = 3
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

    return fix_short_lines(new_lines)



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

def append_missing_lines(new_lines, first, shape):
    y = new_lines[-1][0][1] - new_lines[-2][0][1]
    x1 = new_lines[-1][0][0]
    x2 = new_lines[-1][1][0]
    if len(new_lines)-first >= 46:
        return True
    elif new_lines[-1][0][1]+y < shape[0] and new_lines[-1][1][1]+y < shape[0]:
        new_lines.append([[x1,new_lines[-1][0][1]+y],[x2,new_lines[-1][1][1]+y]])
        return False
    else:
        new_lines.append([[x1,new_lines[-1][0][1]+y],[x2,new_lines[-1][1][1]+y]])
        return True


def fix_short_lines(lines, percentage=85):
    sub = lines[0][1][0] - lines[0][0][0]
    thresh = sub*percentage//100+lines[0][0][0]
    average_horizontal = np.average([x[1][0] for x in lines])
    for x in range(2, len(lines)):
        if lines[x][1][0] < thresh:
            difference = lines[x-1][1][1] - lines[x-2][1][1]
            lines[x][1][0] = int(average_horizontal)
            lines[x][1][1] = lines[x-1][1][1] + difference

    return lines

def get_attendance(image, new_lines, count_threshold=500, roll_no_start=1, left=True, first_line_idx=0):
    append_missing_lines(new_lines, first_line_idx, image.shape)
    attendance_count = []
    roll_no = roll_no_start
    for line_idx in tqdm(range(first_line_idx, len(new_lines)-1)):
        l1 = new_lines[line_idx]
        l2 = new_lines[line_idx+1]
        slope1, const1 = get_line_equation(l1[0], l1[1])
        slope2, const2 = get_line_equation(l2[0], l2[1])
        thresh = 150
        pixels = []

        #TODO Hardcoded
        if left:
            range1, range2 = min(l1[0][1], l1[1][1])+3, max(l2[0][1], l2[1][1])-4
        else:
            range1, range2 = max(l1[0][1], l1[1][1])+4, min(l2[0][1], l2[1][1])
        for x in range(range1, range2):
            if left:
                for y in range(l1[0][0], image.shape[1]//2):
                    if(is_below(slope1, const1, [y,x]) and not is_below(slope2, const2, [y,x])):
                        pixels.append(image[x][y])
            else:
                #TODO Hardcoded
                for y in range(l1[0][0], image.shape[1]-60):
                    if(is_below(slope1, const1, [y,x]) and not is_below(slope2, const2, [y,x])):
                        pixels.append(image[x][y])


        count = 0
        for x in pixels:
            if x < thresh:
                count+=1
        if count > count_threshold:
            #attendance_count.append(f"{roll_no}, P, count {count}")
            attendance_count.append(f"{roll_no}:P")
        else:
            #attendance_count.append(f"{roll_no}, A, count {count}")
            attendance_count.append(f"{roll_no}:A")
        roll_no += 1
    return attendance_count



def run_all_commands(image):
    image = cv2.resize(image, (image.shape[1]//3, image.shape[0]//3))
    orig2 = image.copy()    # Used in trim function to remove horizontal lines
    orig = image.copy()

    idxa = get_vert_line(image)
    left_lines = get_horizontal_lines(img=image, idxs=idxa, horizontal_check=7)
    left_lines = trim_lines(left_lines, orig2)
    # TODO 30 is hardcoded
    idxb = [image.shape[1]//2+30 for x in range(image.shape[0])]
    right_lines = get_horizontal_lines(img=image, idxs=idxb, horizontal_check=7)
    right_lines = trim_lines(right_lines, orig2)

    trimmed_left_lines = get_final_lines(left_lines)
    trimmed_right_lines = get_final_lines(right_lines)
    left_line_idx = get_first_att_line(trimmed_left_lines, image.shape, 60)
    right_line_idx = get_first_att_line(trimmed_right_lines, image.shape, 40)

    image = orig2
    attendance_count_right = get_attendance(image, trimmed_right_lines, count_threshold=450, roll_no_start=46,
                                      left=False, first_line_idx=right_line_idx)
    attendance_count_left = get_attendance(image, trimmed_left_lines, count_threshold=500, roll_no_start=1,
                                      left=True, first_line_idx=left_line_idx)
    attendance_all = attendance_count_left + attendance_count_right
    cv2.drawContours(orig, np.array(trimmed_right_lines), -1, (0, 0, 0), 2)
    cv2.imwrite("output/new.jpg", orig)
    return attendance_all



if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required = True,
    help = "Path to the image to be scanned")
    args = vars(ap.parse_args())

    IMAGE = args["image"]

    image = cv2.imread(IMAGE)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    print(run_all_commands(image))


