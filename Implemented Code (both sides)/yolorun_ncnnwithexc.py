from ultralytics import YOLO
from ultralytics import solutions
import glob
import time
import cv2
import numpy as np


def is_center_inside(inner_box, outer_box, margin):

    center_x = (inner_box[0] + inner_box[2]) / 2
    center_y = (inner_box[1] + inner_box[3]) / 2

    expanded_outer = [
        outer_box[0] - margin,
        outer_box[1] - margin,
        outer_box[2] + margin,
        outer_box[3] + margin

    ]
    
    
    return (expanded_outer[0] <= center_x <= expanded_outer[2] and 
            expanded_outer[1] <= center_y <= expanded_outer[3])


start_time = time.time()

model = YOLO('yolomodel2_ncnn_model', task='detect')




weaknessCount = 0
fakeWeakness = 0
isValidCount = 0


results = model.predict('runImages', device='cpu')

for result in results:
    isValidCount = 0
    if result.boxes is not None:
        img = result.orig_img
        
        detected_classes = [model.names[int(cls)] for cls in result.boxes.cls]
        
        
        if "weakness" in detected_classes:
            if "death_star" in detected_classes:

                death_star_boxes = []
                weakness_boxes = []

                for box in result.boxes:
                    class_name = model.names[int(box.cls)]
                    xyxy = box.xyxy[0].cpu().numpy()

                    if class_name == "death_star":
                        death_star_boxes.append(xyxy)
                    elif class_name == "weakness":
                        weakness_boxes.append((box, xyxy))

                for box, weakness_xyxy in weakness_boxes:
                    is_valid = False
                    
                    for ds_xyxy in death_star_boxes:
                        if is_center_inside(weakness_xyxy, ds_xyxy, 20):
                            is_valid = True
                            break
                        
                    if is_valid:
                        x1, y1, x2, y2 = map(int, weakness_xyxy)
                        cropped_img = img[y1:y2, x1:x2]
                        weaknessCount += 1
                        isValidCount += 1
                        print(f"Image contains weakness)")
                        if isValidCount == 1:
                            img_name = "sample-images/weakness" + str(weaknessCount) + ".png"
                            img_nameTwo = "fullImages/weakness" + str(weaknessCount) + ".png"
                            result.save(img_nameTwo)
                            cv2.imwrite(img_name, cropped_img)
                        else:
                            print("Only one valid weakness can be used")  
                    else:
                        fakeWeakness += 1
                        img_name3 = "fakeWeakness/fakeWeakness" + str(fakeWeakness) + ".png"
                        result.save(img_name3)
                        print("Weakness detected outside of death star")

        else:
            print("No weakness detected in this image")           
end_time = time.time()
totalTime = end_time - start_time
print(f"Total time: {totalTime} seconds")