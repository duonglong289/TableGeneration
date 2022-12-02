import os
from tqdm import tqdm
import cv2
import numpy as np
import argparse
import glob
import json

def parse_line(info):
    file_name = info['filename']
    cells = info['html']['cells'].copy()
    structure = info['html']['structure']['tokens'].copy()
    data = {
        'cells': cells,
        # 'structure': structure,
        'file_name': file_name
    }
    return data


def draw_bbox(img, points, color=(255, 0, 0), thickness=4):
    img = img.copy()
    y_min, x_min = img.shape[:2]
    x_max, y_max = 0, 0
    for point in points:
        x1 = np.min(point[..., 0])
        y1 = np.min(point[..., 1])
        x2 = np.max(point[..., 0])
        y2 = np.max(point[..., 1])
        if x_min > x1: x_min = x1
        if y_min > x1: y_min = y1
        if x_max < x2: x_max = x2
        if y_max < y2: y_max = y2
        cv2.polylines(img, [point.astype(int)], True, color, thickness)
    # table_polygon = [[x1, y1]]

    cv2.rectangle(img, (x_min, y_min), (x_max, y_max), color=color, thickness=thickness)
    return img

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_dir', type=str, default='/mnt/ssd/techainer/table_project/TableGeneration/output/simple_table_02122022')
    parser.add_argument('--gt_dir', type=str, default='/mnt/ssd/techainer/table_project/TableGeneration/output/simple_table_02122022/json')
    parser.add_argument('--output_dir', type=str, default='/mnt/ssd/techainer/table_project/TableGeneration/output/simple_table_02122022')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    list_gt_path = glob.glob(os.path.join(args.gt_dir, "*.json"))
    
    for gt_path in tqdm(list_gt_path):
        with open(gt_path, "rb") as f:
            data_lines = json.load(f)
        data = parse_line(data_lines)
        img_path = os.path.join(args.image_dir, data['file_name'])
        raw_img = cv2.imread(img_path)

        boxes = [np.array(x['bbox']) for x in data['cells']]
        image_name = os.path.basename(img_path).replace("jpg", "png")
        wid, hei = raw_img.shape[:2]
        mask = np.zeros((wid, hei), dtype=np.uint8)
        show_img = draw_bbox(mask, boxes)
        output_dir = os.path.join(args.output_dir, 'mask')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, image_name)
        cv2.imwrite(output_path, show_img)
