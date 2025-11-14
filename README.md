# Senior Design II (CEG4981) | Fall 2025 | Group 2's Project Repository
### Team Members
- Ben Hawk (Computer Engineering) - `hawk.38@wright.edu` 
  - Worked on the Image Identification programs via YoloV11 very extensively.
- Zachary Kramer (Electrical Engineering) - `kramer.129@wright.edu`
  - Worked on Python NRF24L01 transmitting and receiving programs, as well as Raspberry Pi implementation & wiring.
- Kyle Cox (Computer Science) - `cox.362@wright.edu` 
  - Worked on Python encryption, decryption, MD5 generation, USB detection, and other programs. Also organized most of the GitHub repository.
- Ryan Shanley (IT & Cyber) - `shanley.4@wright.edu` 
  - Worked on our original cropping program, set up the mobile app & Flask server.

### Problem Statement
Ever since their takeover, the Empire’s rule has led to extensive amounts of death and destruction. Most of this destruction was accomplished by their huge, powerful weapon, the Death Star. Issues will begin to rise in the Galaxy if this tyrannic rule continues.
Taking down this weapon not only would prevent destruction but would also be the first step in retaking control of the Galaxy. Within the Death Star contains vulnerability plans which can be used to disable the weapon, but they need to be obtained in a way that is both hasty and covert.

### Proposed Solution
Use a non-standard communication method, specifically radio frequency transmission, to obtain the Death Star plans, and send them from a Raspberry Pi to a Rebel Server, where they will be transferred to a mobile app to be displayed to the public. This public display of the plans will allow the Death Star to be destroyed. Compared to existing standard communications, using a non-standard method heavily reduces the chances of being detected, which would be key to avoid for this plan. Compared to a physical invasion to obtain the Death Star plans, using a non-standard communication method is much safer and covert.

## Project Breakdown
### Folder Guide
- **Encryption Side & Decryption Side**: Some iterations of our code, organized by each side.
- **Implemented Code (both sides)**: The *actual code* implemented on the Raspberry Pi.
- **yolomodel2.0**: The YoloV11 Model that was trained and used within this design.
- **DeathStarMobileApp**: The code for the Mobile App.

### Encryption & Transmitting Side
- **USB Insert Processing**: Copying .png images from a USB drive automatically once it is inserted. (Relevant File: `usb-detection.py`) 
- **Image Identification**: Training the Yolo-V11 image identification program to specifically detect images that contain the Death Star with a red vulnerability circle on them. Any detected images will be thrown into a folder as verified vulnerability images. (Relevant File: `yolorun.py`, also see the `yolomodel2.0` folder)
  - **Image Cropping**: Cropping the images utilizing the Yolo-V11 image identification program to specifically show the red circles, which indicate the vulnerability locations.
- **Encryption and MD5 Checksum generation**: Using Python, taking each image in a provided folder from the previous step, generating a MD5 checksum for the image via hashlib, and encrypting the image using the AES-128 encryption algorithm via pycryptodome. The encrypted image and the MD5 are paired together for transmission. (Relevant File: `encryption.py`)
- **Transmitting via NRF24L01**: Transmitting each image binary file over using the NRF24L01 radio transmitter connected to the Raspberry Pi. This is run through a Python script, using the RF24 Python library. (Relevant File: `transmitter.py`)
### Decrypting & Receiving Side 
- **Receiving via NRF24L01**: Receiving each image binary file using the NRF24L01 radio transmitter connected to the "Rebel Server". This is run through a Python script, using the RF24 Python library. (Relevant File: `receiver.py`) 
- **Decryption and MD5 Checksum generation/comparison**: Using Python, taking each received file in a provided folder from the transmission, decrypting the results to obtain an image via pycryptodome, generating a MD5 checksum for that image via hashlib, and then comparing the checksums to see if they match. If they match, the image is verified to be decrypted properly, and is added to a results folder. (Relevant File: `decryption.py`)
- **Image Cropping**: ~~Taking each image in the results folder and using OpenCV to crop the images to show specifically the vulnerability located indicated by the red circle on the images. These images are saved to a new folder.~~ Moved to Encryption Side during development. (Relevant File: `Image-Cropping.py.disabled`)
- **Transmit Results to Mobile App**: Files from the folder created in the step above are send to a mobile app that runs with Android Studio. This mobile app displays the images, and allows users to download them to their own system. Thus, the vulnerability images are officially exposed, hopefully accomplishing our goal of eventually destroying the Death Star. (Relevant Folder: `DeathStarMobileApp`)

### Project Demo Screenshots
#### Transmitting Side Box
*A picture showing the trasmitting side of the communication, with the Raspberry Pi plugged into a monitor.*
![Transmitting Side Box](./Documentation%20Images/demo-box.png)
#### Receiving Side Files
*A picture showing the receiving side of the communication, with files received (encrypted .bin files, .txt files for md5 checksum checking)*
![Receiving Side Files](./Documentation%20Images/demo-files.png)
#### YoloV11 Demonstration
*A picture showing an example of the YoloV11 model identifying certain objects. While we only needed to identify red circles in this project, the additional identification helped increase accuracy of our model.*
![YoloV11 Demonstration](./Documentation%20Images/demo-yolo.png)
#### Mobile App Demonstration
*A picture showing the cropped images on our Mobile App, running through an Android simulator.*
![Mobile App Demonstration](./Documentation%20Images/demo-app.png)
