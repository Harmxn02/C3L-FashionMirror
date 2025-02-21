from fastapi import FastAPI, File, UploadFile
import uvicorn
import numpy as np
import cv2
from PIL import Image
from transformers import pipeline
import webcolors
import torch


import warnings
warnings.filterwarnings("ignore", category=FutureWarning)


app = FastAPI()


from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all domains (change this in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)









# Load Hugging Face models
segmentation_pipe = pipeline(
    "image-segmentation",
    model="mattmdjaga/segformer_b2_clothes",
    device=0 if torch.cuda.is_available() else -1
)

hair_color_pipe = pipeline(
    "image-classification",
    model="enzostvs/hair-color",
    device=0 if torch.cuda.is_available() else -1
)

EXCLUDED_CLASSES = {"Background"}


def closest_color(requested_color):
    """
    Finds the closest named color using webcolors.
    """
    min_colours = {}
    for name in webcolors.names("css3"):
        r_c, g_c, b_c = webcolors.name_to_rgb(name)
        rd = (r_c - requested_color[0]) ** 2
        gd = (g_c - requested_color[1]) ** 2
        bd = (b_c - requested_color[2]) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]


def detect_color(frame, mask):
    """
    Detects the median color of the segmented clothing region.
    """
    masked_pixels = frame[mask > 0]
    if masked_pixels.size == 0:
        return "Unknown"
    median_color = np.median(masked_pixels, axis=0)
    return closest_color(tuple(map(int, median_color)))


@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    """
    Receives an image, processes it with Hugging Face models, 
    and returns detected hair and clothing colors.
    """
    image = Image.open(file.file).convert("RGB")
    frame = np.array(image)

    # Run segmentation model
    results = segmentation_pipe(image)

    detected_items = []

    for result in results:
        label = result['label']
        if label in EXCLUDED_CLASSES:
            continue
        
        mask = np.array(result['mask'])

        if label == "Hair":
            # Use hair classification model
            hair_result = hair_color_pipe(image)
            color_name = hair_result[0]['label']
        else:
            # Detect clothing color
            color_name = detect_color(frame, mask)

        detected_items.append(f"{label} ({color_name})")

    print(f"Detected items: {detected_items if detected_items else "No items detected"}")
    return {"detected": " - ".join(detected_items) if detected_items else "No items detected"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
