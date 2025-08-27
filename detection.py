# Importing Required Packages
import cv2
import pandas as pd
from ultralytics import YOLO
import os

# Load your trained YOLO models
model_parts = YOLO(r"C:\Users\Webbies\Jupyter_Notebooks\CarInsuranceInspection\CarPart.pt")
model_damage = YOLO(r"C:\Users\Webbies\Jupyter_Notebooks\CarInsuranceInspection\CarDamage.pt")

# Computing the IOU score between two boxes
def compute_iou(boxA, boxB):
    """Compute Intersection over Union (IoU) between two boxes.
    Boxes are (x1, y1, x2, y2)."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    interArea = interW * interH

    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    unionArea = float(boxAArea + boxBArea - interArea)
    if unionArea == 0:
        return 0.0

    return interArea / unionArea

# Define a function to detect the detections and report making
def modified_damage_detection_report(video_path, custom_base_name=None):
    # Extract base name of video (without extension)
    if custom_base_name:
        base_name = os.path.splitext(custom_base_name)[0]
    else:
        base_name = os.path.splitext(os.path.basename(video_path))[0]

    # Auto-generate output names
    output_video = f"{base_name}_detected.mp4"
    output_excel = f"{base_name}_report.xlsx"

    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))

    # Video writer for detected video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (frame_width, frame_height))

    frame_num = 0
    report_data = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_num += 1

        # Detect car parts
        results_parts = model_parts(frame)
        parts_boxes = results_parts[0].boxes

        # Detect damages
        results_damage = model_damage(frame)
        damage_boxes = results_damage[0].boxes

        # Only process if at least one damage is detected
        if len(damage_boxes) > 0:
            for db in damage_boxes:
                dx1, dy1, dx2, dy2 = db.xyxy[0]
                dconf = float(db.conf[0])
                dclass = int(db.cls[0])
                dlabel = model_damage.names[dclass]

                damage_box = (float(dx1), float(dy1), float(dx2), float(dy2))

                matched_part = "Unknown"
                severity = "Low"
                best_iou = 0.0

                for pb in parts_boxes:
                    px1, py1, px2, py2 = pb.xyxy[0]
                    pclass = int(pb.cls[0])
                    plabel = model_parts.names[pclass]

                    part_box = (float(px1), float(py1), float(px2), float(py2))
                    iou = compute_iou(damage_box, part_box)

                    if iou > best_iou:
                        best_iou = iou
                        matched_part = plabel

                # Rule-based severity by IoU overlap
                if best_iou > 0.5:
                    severity = "High"
                elif best_iou > 0.3:
                    severity = "Medium"
                else:
                    severity = "Low"

                # Convert frame index → timestamp in seconds
                timestamp_sec = round(frame_num / fps, 2)

                report_data.append({
                    "Frame": frame_num,
                    "Time(s)": timestamp_sec,
                    "Car_Part": matched_part,
                    "Damage_Type": dlabel,
                    "Damage_Confidence": round(dconf, 2),
                    "Severity": severity
                })

                # Draw bbox on frame
                cv2.rectangle(frame, (int(dx1), int(dy1)), (int(dx2), int(dy2)), (255, 0, 0), 5)
                label_text = f"{matched_part} | {dlabel} | {dconf:.2f}"
                cv2.putText(frame, label_text, (int(dx1), int(dy1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2, cv2.LINE_AA)

        out.write(frame)

    cap.release()
    out.release()

    # Ensure Excel always has headers
    columns = ["Frame", "Time(s)", "Car_Part", "Damage_Type", "Damage_Confidence", "Severity"]
    df = pd.DataFrame(report_data, columns=columns)
    df.to_excel(output_excel, index=False)

    if len(report_data) == 0:
        print(f"No damages detected.\nVideo saved: {output_video}\nEmpty report saved: {output_excel}")
    else:
        print(f"Detection complete!\nVideo saved: {output_video}\nReport saved: {output_excel}")

    return output_video, output_excel