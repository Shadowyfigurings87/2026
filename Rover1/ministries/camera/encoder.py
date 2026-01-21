import cv2

def encode_jpeg(frame, quality=80):
    ret, jpeg = cv2.imencode(
        ".jpg",
        frame,
        [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)],
    )
    if not ret:
        raise RuntimeError("JPEG encode failed")
    return jpeg.tobytes()
