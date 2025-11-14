import tensorflow as tf
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, BatchNormalization, Concatenate
from tensorflow.keras.layers import Flatten, Dense
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import load_model
import numpy as np
import time
import os
import cv2
from io import BytesIO
import math
import tempfile
from datetime import datetime, timedelta


def predict(data, width, height, videoduration):
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    parent_dir = os.path.dirname(current_dir)
    models_and_harrcascade=os.path.join(parent_dir, 'emo','models_and_harrcascade')
    model1_path = os.path.join(models_and_harrcascade, 'base_grayscale_model.h5')
   
    model2_path = os.path.join(models_and_harrcascade, 'base_grayscale_model_2.h5')
   
    model3_path = os.path.join(models_and_harrcascade, 'kaggle_grayscale_model.h5')
   
    model4_path = os.path.join(models_and_harrcascade, 'kaggle_grayscale_model2.h5')
    model1 = load_model(model1_path)
    model2 = load_model(model2_path)
    model3 = load_model(model3_path)
    model4 = load_model(model4_path)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    channels = 3
    width=int(width)
    height=int(height)
    frame_size = height * width * channels
    combined_video_data = b''
        
    
    total_frames=0

    for chunk in data:
        for chunk_data in chunk.chunks():
            total_frames+=1
            combined_video_data += chunk_data
    
    
    video_stream = BytesIO(combined_video_data)
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(video_stream.getvalue())
        temp_file_path = temp_file.name

  

    cap = cv2.VideoCapture(temp_file_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    # print(fps)
    # print("\n\n\n\n\n\n")
    emotion_history = []

    iterator=0
    while True:
        ret, frame = cap.read()
        if not ret:
            break 
        

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # print(iterator)
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        for (x, y, w, h) in faces:
            face = gray_frame[y:y+h, x:x+w]
            face = np.array(face)
            face = cv2.resize(face, (48, 48))

            face = np.expand_dims(face, axis=0)

            preds_model1 = model1.predict(face)
            preds_model2 = model2.predict(face)
            preds_model3 = model3.predict(face)
            preds_model4 = model4.predict(face)

            weight_model1 = 0.25
            weight_model2 = 0.5
            weight_model3 = 0.25
            weight_model4 = 0.25

            weighted_average_preds = (
                weight_model1 * preds_model1 +
                weight_model2 * preds_model2 +
                weight_model3 * preds_model3 +
                weight_model4 * preds_model4
            )

            predicted_class_index = np.argmax(weighted_average_preds, axis=1)
            integer_to_label = {0: 'angry', 1: 'neutral', 2: 'happy', 3: 'fear', 4: 'disgust', 5: 'sad', 6: 'surprise'}
            predicted_emotion = integer_to_label[predicted_class_index[0]]

            # Get timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            emotion_history.append({'emotion': predicted_emotion, 'timestamp': timestamp})

        iterator+=1
    videoduration2=videoduration
    # videoduration2=math.floor(float(videoduration2)/1000)
    try:
        videoduration2 = float(videoduration2)
        if not math.isfinite(videoduration2):  # handle inf or nan
            videoduration2 = 5000  # default to 5 seconds if invalid
        videoduration2 = math.floor(videoduration2 / 1000)
    except (ValueError, TypeError):
        videoduration2 = 5  # default fallback
    # print("video duration"+str(videoduration2))
    integer_part=videoduration2
    total_emotions=len(emotion_history)
    emotion_lapse=total_emotions/int(integer_part)
    emotion_lapse=int(math.floor(emotion_lapse))
    emotion_history2=[]
    # print("total emotions"+str(total_emotions))
    # print("emotion_lapse"+str(emotion_lapse))
    # print("integerpart " + str(integer_part))
    # print("nnobb\n\n\n")
    # Convert timestamp strings to datetime objects
    for entry in emotion_history:
        entry['timestamp'] = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S.%f')

    # Initialize a starting time
    start_date = emotion_history[0]['timestamp'].date()

    # Initialize a starting time with time set to 00:00:00
    start_time = emotion_history[0]['timestamp'].replace(hour=0, minute=0, second=0, microsecond=0)

    
    # Format the datetime object as per the desired format
    formatted_start_time = start_time.strftime('%Y-%m-%d %H:%M:%S.%f')

    counter=0
    for i in range(0,total_emotions):
        if(i%emotion_lapse==0):
            
            new_entry = emotion_history[i].copy()  # Create a copy of the original entry
                
            new_entry_time = datetime.strptime(formatted_start_time, '%Y-%m-%d %H:%M:%S.%f') + timedelta(seconds=counter * 60)
            new_entry['timestamp'] = new_entry_time.strftime('%Y-%m-%d %H:%M:%S.%f')

            emotion_history2.append(new_entry)
            counter+=1
    # print(counter)
    # print(iterator)
    
    return emotion_history2
