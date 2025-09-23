import cv2
import os                                                #opencv imports
import numpy as np
import sys

folder_path = f"./Decrypted_Images"
save_folder = f"./Cropped_Images"
os.makedirs(save_folder, exist_ok=True)

# Check if the above decrypted images file exists; if not, end program immediately
if not os.path.exists(folder_path):
    print ("ERROR: Required file not detected, ending cropping program!")
    sys.exit()

# Grab all images in Decrypted_Images folder
file_paths = [
    os.path.join(folder_path, f) for f in os.listdir(folder_path)
    if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif"))
]

# Iterate through and crop out the red circles, save to Cropped_Images
if file_paths:                                  
    selected_images = file_paths[:10]           

    if save_folder:
        for i, file_path in enumerate(selected_images):
            img = cv2.imread(file_path)

            if img is not None:
                
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)                  #Changes to hsv color pallete

                lower_red1 = np.array([0, 100, 100])
                upper_red1 = np.array([10, 255, 255])
                lower_red2 = np.array([170, 100, 100])
                upper_red2 = np.array([180, 255, 255])                  #Sets what color red to look for

                mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
                mask2 = cv2.inRange(hsv, lower_red2, upper_red2)        #mask for red arrays
                red_mask = cv2.bitwise_or(mask1, mask2)

                gray = cv2.GaussianBlur(red_mask, (9, 9), 2)

                circles = cv2.HoughCircles(
                    gray, cv2.HOUGH_GRADIENT, dp=1.0, minDist=50,
                    param1=100, param2=15, minRadius=10, maxRadius=0
                )
                
                if circles is not None:
                    circles = np.round(circles[0, :]).astype("int")
                    for j, (x, y, r) in enumerate(circles):

                        mask = np.zeros_like(gray)
                        cv2.circle(mask, (x, y), r, 255, -1)

                        masked_img = cv2.bitwise_and(img, img, mask=mask)

                        x1, y1 = max(0, x-r), max(0, y-r)
                        x2, y2 = min(img.shape[1], x+r), min(img.shape[0], y+r)             #cropping around red circle
                        cropped = masked_img[y1:y2, x1:x2]

                        bgr_with_alpha = cv2.cvtColor(cropped, cv2.COLOR_BGR2BGRA)

                        mask_cropped = mask[y1:y2, x1:x2]

                        bgr_with_alpha[:, :, 3] = mask_cropped

                        save_path = os.path.join(save_folder, f"cropped{i+1}.png")
                        print("Image cropped.")
                        cv2.imwrite(save_path, bgr_with_alpha)
                else:
                    print(f"[WARN] No red circles found in {file_path}")                #debug log

