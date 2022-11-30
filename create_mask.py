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


def draw_bbox(img, points, color=(255, 0, 0), thickness=3):
    img = img.copy()
    for point in points:
        cv2.polylines(img, [point.astype(int)], True, color, thickness)
    return img

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_dir', type=str, default='/mnt/ssd/techainer/table_project/TableGeneration/output/simple_table_21112022')
    parser.add_argument('--gt_dir', type=str, default='/mnt/ssd/techainer/table_project/TableGeneration/output/simple_table_21112022/json')
    parser.add_argument('--output_dir', type=str, default='/mnt/ssd/techainer/table_project/TableGeneration/output/simple_table_21112022/mask')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    list_gt_path = glob.glob(os.path.join(args.gt_dir, "*.json"))
    
    for gt_path in tqdm(list_gt_path):
        with open(gt_path, "rb") as f:
            data_lines = json.load(f)
        data = parse_line(data_lines)

        boxes = [np.array(x['bbox']) for x in data['cells']]
        img_path = os.path.join(args.image_dir, data['file_name'])
        raw_img = cv2.imread(img_path)
        image_name = os.path.basename(img_path)
        wid, hei = raw_img.shape[:2]
        mask = np.zeros((wid, hei), dtype=np.uint8)
        show_img = draw_bbox(mask, boxes)
        output_dir = os.path.join(args.output_dir, 'mask')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, image_name)
        cv2.imwrite(output_path, show_img)
