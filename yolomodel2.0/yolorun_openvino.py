from ultralytics import YOLO
from ultralytics import solutions
import glob
import time
import cv2
import numpy as np

start_time = time.time()

model = YOLO('yolomodel2_openvino_model', task='detect')




weaknessCount = 0


results = model.predict('runImages', device='cpu')

for result in results:
    if result.boxes is not None:

        img = result.orig_img
        
        detected_classes = [model.names[int(cls)] for cls in result.boxes.cls]
        
        
        if "weakness" in detected_classes:
            if "death_star" in detected_classes:
                for i, box in enumerate(result.boxes):
                    class_name = model.names[int(box.cls)]

                    if class_name == "weakness":
                        x1, y1, x2, y2 = map(int, box.xyxy[0])

                        cropped_img = img[y1:y2, x1:x2]

                weaknessCount += 1
                print(f"Image contains weakness)")
                img_name = "sample-images/weakness" + str(weaknessCount) + ".png"
                cv2.imwrite(img_name, cropped_img)
        else:
            print("No weakness detected in this image")
end_time = time.time()
totalTime = end_time - start_time
print(f"Total time: {totalTime} seconds")