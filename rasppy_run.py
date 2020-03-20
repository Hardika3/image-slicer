import argparse
from edge import *
from attendance_detection import *
import csv

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required = True,
    help = "Path to the image to be scanned")
args = vars(ap.parse_args())

# load the image and compute the ratio of the old height
# to the new height, clone it, and resize it
image = cv2.imread(args["image"])
warped = document_detect(image)
del warped
warped_img = cv2.imread("output/warped_thresh.jpg")
warped_img = cv2.cvtColor(warped_img, cv2.COLOR_BGR2GRAY)

attendance = run_all_commands(warped_img)

with open('output/attendance.csv', 'w') as f:
    writer = csv.writer(f)
    cols = ['course', '--']
    writer.writerow(cols)
    for x in attendance:
        writer.writerow(x.split(':'))
