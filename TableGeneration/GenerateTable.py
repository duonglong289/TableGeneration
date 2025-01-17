import json
import os
import sys
import random
import string
from PIL import Image
from io import BytesIO
from tqdm import tqdm
import numpy as np
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from TableGeneration.Table import Table


class GenerateTable:
    def __init__(self,
                 output,
                 ch_dict_path,
                 en_dict_path,
                 cell_box_type='cell',
                 min_row=3,
                 max_row=20,
                 min_col=3,
                 max_col=10,
                 max_span_row_count=3,
                 max_span_col_count=3,
                 max_span_value=20,
                 min_txt_len=2,
                 max_txt_len=7,
                 color_prob=0,
                 cell_max_width=0,
                 cell_max_height=0,
                 browser='chrome',
                 browser_width=1920,
                 browser_height=1920,
                 border_type='full'):
        self.output = output  # wheter to store images separately or not
        self.ch_dict_path = ch_dict_path
        self.en_dict_path = en_dict_path
        self.cell_box_type = cell_box_type  # cell: use cell location as cell box; text: use location of text in cell as cell box
        self.min_row = min_row  # minimum number of rows in a table (includes headers)
        self.max_row = max_row  # maximum number of rows in a table
        self.min_col = min_col  # minimum number of columns in a table
        self.max_col = max_col  # maximum number of columns in a table
        self.max_txt_len = max_txt_len  # maximum number of chars in a cell
        self.min_txt_len = min_txt_len  # minimum number of chars in a cell
        self.color_prob = color_prob  # color cell prob
        self.cell_max_width = cell_max_width  # max cell w
        self.cell_max_height = cell_max_height  # max cell h
        self.max_span_row_count = max_span_row_count  # max span row count
        self.max_span_col_count = max_span_col_count  # max span col count
        self.max_span_value = max_span_value  # max span value
        self.browser = browser  # browser used to generate html table
        self.browser_height = browser_height  # browser height
        self.browser_width = browser_width  # browser width
        self.border_type = border_type

        if self.browser == 'chrome':
            from selenium.webdriver import Chrome as Browser
            from selenium.webdriver import ChromeOptions as Options
        else:
            from selenium.webdriver import Firefox as Browser
            from selenium.webdriver import FirefoxOptions as Options
        opts = Options()
        opts.add_argument('--headless')
        opts.add_argument('--no-sandbox')
        self.driver = Browser(options=opts)

    def gen_table_img(self, img_count):
        os.makedirs(self.output, exist_ok=True)
        
        for index in tqdm(range(img_count)):
            # data_arr contains the images of generated tables and all_table_categories contains the table category of each of the table
            out = self.generate_table()
            if out is None:
                continue

            im, html_content, structure, contens, border = out
            im, contens = self.clip_white(im, contens)

            output_file_name = f'{border}_{index}'

            # if the image and equivalent html is need to be stored
            os.makedirs(os.path.join(self.output, 'html'), exist_ok=True)
            os.makedirs(os.path.join(self.output, 'img'), exist_ok=True)

            html_save_path = os.path.join(self.output, 'html', f'{output_file_name}.html')
            img_save_path = os.path.join(self.output, 'img', f'{output_file_name}.jpg')
            # with open(html_save_path, encoding='utf-8', mode='w') as f:
            #     f.write(html_content)
            im.save(img_save_path, dpi=(300, 300), quality=95)

            img_file_name = os.path.join('img', f'{output_file_name}.jpg')
            label_info = self.make_ppstructure_label(structure, contens,
                                                        img_file_name)
            output_label_dir = os.path.join(self.output, 'json')
            os.makedirs(output_label_dir, exist_ok=True)
            output_label_path = os.path.join(output_label_dir, f"{border}_{index}.json")

            with open(output_label_path, "w") as f:
                json.dump(label_info, f, ensure_ascii=False, indent=4)

        self.close()

    def gen_table_img_single(self, index: int):
        out = self.generate_table()
        if out is None:
            return

        im, html_content, structure, contens, border = out
        im, contens = self.clip_white(im, contens)

        output_file_name = f'{border}_{index}'

        # if the image and equivalent html is need to be stored
        os.makedirs(os.path.join(self.output, 'html'), exist_ok=True)
        os.makedirs(os.path.join(self.output, 'img'), exist_ok=True)

        html_save_path = os.path.join(self.output, 'html', f'{output_file_name}.html')
        img_save_path = os.path.join(self.output, 'img', f'{output_file_name}.jpg')
        with open(html_save_path, encoding='utf-8', mode='w') as f:
            f.write(html_content)
        im.save(img_save_path, dpi=(300, 300))

        img_file_name = os.path.join('img', f'{output_file_name}.jpg')
        label_info = self.make_ppstructure_label(structure, contens, img_file_name)
        output_label_dir = os.path.join(self.output, 'json')
        os.makedirs(output_label_dir, exist_ok=True)
        output_label_path = os.path.join(output_label_dir, f"{border}_{index}.json")

        with open(output_label_path, "w") as f:
            json.dump(label_info, f, ensure_ascii=False, indent=4)

    def generate_table(self):
        cols = random.randint(self.min_col, self.max_col)
        rows = random.randint(self.min_row, self.max_row)
        try:
            # initialize table class
            table = Table(self.ch_dict_path, self.en_dict_path,
                          self.cell_box_type, rows, cols, self.min_txt_len,
                          self.max_txt_len, self.max_span_row_count,
                          self.max_span_col_count, self.max_span_value,
                          self.color_prob, self.cell_max_width,
                          self.cell_max_height, border_type=self.border_type)
            # get table of rows and cols based on unlv distribution and get features of this table
            # (same row, col and cell matrices, total unique ids, html conversion of table and its category)
            id_count, html_content, structure, border = table.create()

            # convert this html code to image using selenium webdriver. Get equivalent bounding boxes
            # for each word in the table. This will generate ground truth for our problem
            
            im, contens = self.html_to_img(html_content, id_count)
            return im, html_content, structure, contens, border
        except KeyboardInterrupt:
            import sys
            sys.exit()
        except Exception:
            import traceback
            traceback.print_exc()
            return None

    def make_ppstructure_label(self, structure, bboxes, img_path):
        d = {
            'filename': img_path,
            'html': {
                'structure': {
                    'tokens': structure
                }
            }
        }
        cells = [{'tokens': list(bbox[1]), 'bbox': bbox[2:]} for bbox in bboxes]
        d['html']['cells'] = cells
        d['gt'] = self.rebuild_html_from_ppstructure_label(d)
        return d

    def rebuild_html_from_ppstructure_label(self, label_info):
        from html import escape
        html_code = label_info['html']['structure']['tokens'].copy()
        to_insert = [
            i for i, tag in enumerate(html_code) if tag in ('<td>', '>')
        ]
        for i, cell in zip(to_insert[::-1], label_info['html']['cells'][::-1]):
            if cell['tokens']:
                cell = [
                    escape(token) if len(token) == 1 else token
                    for token in cell['tokens']
                ]
                cell = ''.join(cell)
                html_code.insert(i + 1, cell)
        html_code = ''.join(html_code)
        return f'<html><body><table>{html_code}</table></body></html>'

    def clip_white(self, im, bboxes):
        w, h = im.size
        bbox = np.array([x[2] for x in bboxes])
        xmin = bbox[:, :, 0].min()
        ymin = bbox[:, :, 1].min()
        xmax = bbox[:, :, 0].max()
        ymax = bbox[:, :, 1].max()
        
        # Random crop padding
        # xmin = max(0, xmin - random.randint(0, 10))
        # ymin = max(0, ymin - random.randint(0, 10))
        # xmax = min(w, xmax + random.randint(2, 10))
        # ymax = min(h, ymax + random.randint(2, 10))
        
        # Crop fit bounding box:
        if self.cell_box_type == 'cell':
            xmin = max(0, xmin - 5)
            ymin = max(0, ymin - 5)
            xmax = min(w, xmax + 5)
            ymax = min(h, ymax + 5)
        elif self.cell_box_type == 'text':
            xmin = max(0, xmin - 40)
            ymin = max(0, ymin - 20)
            xmax = min(w, xmax + 40)
            ymax = min(h, ymax + 20)
        im = im.crop([xmin, ymin, xmax, ymax])

        bbox[:, :, 0] -= xmin
        bbox[:, :, 1] -= ymin
        for item, box in zip(bboxes, bbox):
            item[2] = box.tolist()
        return im, bboxes

    def html_to_img(self, html_content, id_count):
        '''converts html to image'''
        self.driver.get(f"data:text/html;charset=utf-8,{html_content}")
        self.driver.maximize_window()
        self.driver.set_window_size(
            width=self.browser_width,
            height=self.browser_height,
            windowHandle="current")
        window_size = self.driver.get_window_size()
        max_height, max_width = window_size['height'], window_size['width']
        # element = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.ID, '0')))
        contens = []
        for id in range(id_count):
            # e = driver.find_element_by_id(str(id))
            e = WebDriverWait(
                self.driver,
                10).until(EC.presence_of_element_located((By.ID, str(id))))
            txt = e.text.strip()
            lentext = len(txt)
            loc = e.location
            size_ = e.size
            xmin = loc['x']
            ymin = loc['y']
            xmax = int(size_['width'] + xmin)
            ymax = int(size_['height'] + ymin)

            contens.append([
                lentext, txt, [[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]]
            ])

        png = self.driver.get_screenshot_as_png()

        im = Image.open(BytesIO(png)).convert('RGB')
        im = im.crop((0, 0, max_width, max_height))
        return im, contens

    def close(self):
        self.driver.stop_client()
        self.driver.quit()
