import random
import numpy as np
import math
from typing import Optional, Tuple, List
from .utils_html import gray_color_name, blue_color_name


def color_to_hex_html(color):
    r, g, b = color
    r_hex = hex(r).replace("0x", "")
    r_hex = f"0{r_hex}" if len(r_hex)==1 else r_hex
    g_hex = hex(g).replace("0x", "")
    g_hex = f"0{g_hex}" if len(g_hex)==1 else g_hex
    b_hex = hex(b).replace("0x", "")
    b_hex = f"0{b_hex}" if len(b_hex)==1 else b_hex
    return f"#{r_hex}{g_hex}{b_hex}"


def load_courp(p, join_c=' '):
    courp = []
    with open(p, mode='r', encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip("\n").strip("\r\n")
            courp.append(line)
    return join_c.join(courp)

class Table:
    def __init__(self,
                 ch_dict_path,
                 en_dict_path,
                 cell_box_type='cell',
                 no_of_rows=14,
                 no_of_cols=14,
                 min_txt_len=2,
                 max_txt_len=7,
                 max_span_row_count=3,
                 max_span_col_count=3,
                 max_span_value=20,
                 color_prob=0,
                 cell_max_width=0,
                 cell_max_height=0,
                 border_type='full_line'):
        assert cell_box_type in [
            'cell', 'text'
        ], "cell_box_type must in ['cell', 'text'],cell: use cell location as cell box; text: use location of text in cell as cell box"
        self.cell_box_type = cell_box_type
        self.no_of_rows = no_of_rows
        self.no_of_cols = no_of_cols
        self.max_txt_len = max_txt_len
        self.min_txt_len = min_txt_len
        self.color_prob = color_prob
        self.cell_max_width = cell_max_width
        self.cell_max_height = cell_max_height
        self.max_span_row_count = max_span_row_count
        self.max_span_col_count = max_span_col_count
        self.max_span_value = max_span_value

        self.ch = load_courp(ch_dict_path, ' ')
        self.en = load_courp(en_dict_path, ' ')

        self.border_type = border_type
        self.spanflag = False
        '''cell_types matrix have five possible values:
            c: ch
            e: en
            n: number
            t: ''
            m: money
        '''
        self.cell_types = np.chararray(shape=(self.no_of_rows,
                                              self.no_of_cols))
        '''headers matrix have two possible values: 's' and 'h' where 'h' means header and 's' means simple text'''
        self.headers = np.chararray(shape=(self.no_of_rows, self.no_of_cols))
        '''A positive value at a position in matrix shows the number of columns to span and -1 will show to skip that cell as part of spanned cols'''
        self.col_spans_matrix = np.zeros(shape=(self.no_of_rows,
                                                self.no_of_cols))
        '''A positive value at a position means number of rows to span and -1 will show to skip that cell as part of spanned rows'''
        self.row_spans_matrix = np.zeros(shape=(self.no_of_rows,
                                                self.no_of_cols))
        '''missing_cells will contain a list of (row,column) pairs where each pair would show a cell where no text should be written'''
        self.missing_cells = []


    def get_log_value(self):
        ''' returns log base 2 (x)'''
        return int(math.log(self.no_of_rows * self.no_of_cols, 2))

    def define_col_types(self):
        '''
        We define the data type that will go in each column. We categorize data in three types:
        1. 'n': Numbers
        2. 'w': word
        3. 'r': other types (containing special characters)
        '''

        prob_words = 0.3 # Chinese
        prob_numbers = 0.4
        prob_ens = 0.4
        prob_money = 0.2
        for i, type in enumerate(
                random.choices(
                    ['n', 'm', 'e'],
                    weights=[prob_numbers, prob_money, prob_ens],
                    k=self.no_of_cols)):
            self.cell_types[:, i] = type
        '''The headers should be of type word'''
        self.cell_types[0:2, :] = 'e'
        
        # Header bold text
        ratio_header = random.random()
        if ratio_header < 0.05:
            num_row_header = self.no_of_rows
        elif ratio_header < 0.2:
            num_row_header = 0
        else:
            num_row_header = random.randint(1, 2)

        '''All cells should have simple text but the headers'''
        self.headers[:] = 's' # simple text
        self.headers[0:num_row_header, :] = 'h' # header

        # header_count will keep track of how many top rows and how many left columns are being considered as headers
        self.header_count = {'r': num_row_header, 'c': 0}

    def generate_random_text(self, type):
        '''cell_types matrix have two possible values:
            c: chinese
            e: english
            n: number
            t: ''
            m: money

        '''
        if type in ['n', 'm']:
            max_num = random.choice([10, 100, 1000, 10000])
            if random.random() < 0.5:
                out = '{:.2f}'.format(random.random() * max_num)
            elif random.random() < 0.7:
                out = '{:.0f}'.format(random.random() * max_num)
            else:
                # Randomly retain 2 decimal places
                out = str(random.random() *
                          max_num)[:len(str(max_num)) + random.randint(0, 3)]
            if type == 'm':
                out = f'${out}'
        elif (type == 'e'):
            txt_len = random.randint(self.min_txt_len, self.max_txt_len)
            out = self.generate_text(txt_len, self.en)
            # 50% chance to capitalize the first letter
            if random.random() < 0.5:
                out[0] = out[0].upper()
        elif type == 't':
            out = ''
        else:
            txt_len = random.randint(self.min_txt_len, self.max_txt_len)
            out = self.generate_text(txt_len, self.ch)
        return ''.join(out)

    def generate_text(self, txt_len, dict):
        random_star_idx = random.randint(0, len(dict) - txt_len)
        txt = dict[random_star_idx:random_star_idx + txt_len]
        return list(txt)

    def agnostic_span_indices(self, maxvalue, max_num=3):
        '''Spans indices. Can be used for row or col span
        Span indices store the starting indices of row or col spans while span_lengths will store
        the length of span (in terms of cells) starting from start index.'''
        span_indices = []
        span_lengths = []
        # random select span count
        span_count = random.randint(1, max_num)
        if (span_count >= maxvalue):
            return [], []

        indices = sorted(random.sample(list(range(maxvalue)), span_count))

        # get span start idx and span value
        starting_index = 0
        for i, index in enumerate(indices):
            if (starting_index > index):
                continue

            max_lengths = maxvalue - index
            if (max_lengths < 2):
                break
            len_span = random.randint(1, min(max_lengths, self.max_span_value))

            if (len_span > 1):
                span_lengths.append(len_span)
                span_indices.append(index)
                starting_index = index + len_span

        return span_indices, span_lengths

    def make_first_row_spans(self):
        '''This function spans first row'''
        while (True):  # iterate until we get some first row span indices
            header_span_indices, header_span_lengths = self.agnostic_span_indices(
                self.no_of_cols, self.max_span_col_count)
            if (len(header_span_indices) != 0 and
                    len(header_span_lengths) != 0):
                break

        # make first row span matric
        row_span_indices = []
        self.spanflag = True
        for index, length in zip(header_span_indices, header_span_lengths):
            self.col_spans_matrix[0, index] = length
            self.col_spans_matrix[0, index + 1:index + length] = -1
            row_span_indices += list(range(index, index + length))

        # for not span cols, set it to row span value 2
        b = list(
            filter(lambda x: x not in row_span_indices,
                   list(range(self.no_of_cols))))
        self.row_spans_matrix[0, b] = 2
        self.row_spans_matrix[1, b] = -1

    def make_first_col_spans(self):
        '''To make some random row spans on first col of each row'''
        colnumber = 0
        # skip top 2 rows of header
        span_indices, span_lengths = self.agnostic_span_indices(
            self.no_of_rows - 2, self.max_span_row_count)
        span_indices = [x + 2 for x in span_indices]

        self.spanflag = True
        for index, length in zip(span_indices, span_lengths):
            self.row_spans_matrix[index, colnumber] = length
            self.row_spans_matrix[index + 1:index + length, colnumber] = -1
        self.headers[:, colnumber] = 'h'
        self.header_count['c'] += 1

    def generate_missing_cells(self):
        '''This is randomly select some cells to be empty (not containing any text)'''
        missing = np.random.random(size=(self.get_log_value(), 2))
        missing[:, 0] = (self.no_of_rows - 1 - self.header_count['r']
                         ) * missing[:, 0] + self.header_count['r']
        missing[:, 1] = (self.no_of_rows - 1 - self.header_count['c']
                         ) * missing[:, 1] + self.header_count['c']
        for arr in missing:
            self.missing_cells.append((int(arr[0]), int(arr[1])))

    def create_border_style(self):
        if self.border_type =='full_line':
            tab_thick = random.choices([1, 2, 3, 4], weights=[0.2, 0.35, 0.35, 0.1], k=1)[0]
            th_thick = random.choices([1, 2, 3, 4], weights=[0.25, 0.35, 0.5, 0.05], k=1)[0]
            td_thick = min(th_thick, random.choices([1, 2, 3, 4], weights=[0.25, 0.35, 0.35, 0.05], k=1)[0])
            
            r_color = random.random()
            if r_color < 0.0:
                # Generate 3D border, no color
                color = ''
                type_lines = ['groove', 'ridge', 'inset', 'outset']
                type_line = random.choice(type_lines)
            else: # Generate normal border
                # Selenium WebElement raise timeout when using color with hex
                # r_c = random.randint(0, 50)
                # g_c = max(0, r_c + random.randint(-8, 7))
                # b_c = max(0, r_c + random.randint(-8, 7))
                # color = color_to_hex_html((r_c, g_c, b_c))

                # Using color name instead
                color = random.choice(gray_color_name)
                type_lines = ['dashed', 'dotted', 'double', 'solid']
                ratio = [0.15, 0.15, 0.15, 0.55]
                type_line = random.choices(type_lines, weights=ratio, k=1)[0]
            
            style = {
                'name': 'full_line_border',
                'style': {
                    'table': f'border:{tab_thick}px {type_line}; border-color: {color};',
                    'td': f'border:{td_thick}px {type_line}; border-color: {color};',
                    'th': f'border:{th_thick}px {type_line}; border-color: {color};'
                },
            }
        elif self.border_type == 'partial_line':
            tab_thick = 1
            td_thick = 1
            th_thick = 1
            partial_line_type = {
                1: {
                    'name': 'border_top',
                    'style': {
                        'table': f'border-top: {tab_thick}px solid black;',
                        'td': f'border-top: {td_thick}px solid black;',
                        'th': f'border-top: {th_thick}px solid black;'
                    }
                },
                3: {
                    'name': 'border_bottom',
                    'style': {
                        'table': f'border-bottom: {tab_thick}px solid black;',
                        'td': f'border-bottom: {td_thick}px solid black;',
                        'th': f'border-bottom: {th_thick}px solid black;'
                    }
                },
                4: {
                    'name': 'head_border_bottom',
                    'style': {
                        'th': f'border-bottom: {th_thick}px solid black;'
                    }
                },
                6: {
                    'name': 'border_left',
                    'style': {
                        'table': f'border-left: {tab_thick}px solid black;',
                        'td': f'border-left: {td_thick}px solid black;',
                        'th': f'border-left: {th_thick}px solid black;'
                    }
                },
                7: {
                    'name': 'border_right',
                    'style': {
                        'table': f'border-right: {tab_thick}px solid black;',
                        'td': f'border-right: {td_thick}px solid black;',
                        'th': f'border-right: {th_thick}px solid black;'
                    }
                }
            }
        else: # No line
            style = {
                    'name': 'no_border',
                    'style': ''
                }
        return style

    def create_table_data_style(self, border_style):
        td_style = "td{"
        # Vertical alignment
        vertical_align = random.choices(['top', 'bottom', 'center'], weights=[0.3, 0.2, 0.5], k=1)[0]
        td_style += f"vertical-align: {vertical_align};"
        # Set padding table data
        if random.random() < 0.8:
            pad_d_top = random.randint(1, 8)
            pad_d_bot = random.randint(1, 8)
            pad_d_left = random.randint(1, 15)
            pad_d_right = random.randint(1, 15)
        else:
            pad_d_top = pad_d_bot = pad_d_left = pad_d_right = 0
        td_style += f"padding-top: {pad_d_top}px;"
        td_style += f"padding-bottom: {pad_d_bot}px;"
        td_style += f"padding-left: {pad_d_left}px;"
        td_style += f"padding-right: {pad_d_right}px;"
        # Set word break
        # Text wrapping - break the line
        td_style += "word-break: break-word;"
        # Set limit size
        # Only need to set the height of the table header; don't need to set the height of the table data.
        # if self.cell_max_height != 0:
        #     td_style += f"height: {random.randint(self.cell_max_height // 2, self.cell_max_height)}px;"
        if self.cell_max_width != 0:
            td_style += f"width: {random.randint(self.cell_max_width // 4, self.cell_max_width)}px;"
        # Set border style
        if 'td' in border_style:
            td_style += border_style['td']
        
        td_style += "}"
        return td_style

    def create_table_header_style(self, border_style):
        th_style = "th{"
        # Vertical alignment
        vertical_align = random.choices(['top', 'bottom', 'center'], weights=[0.3, 0.2, 0.5], k=1)[0]
        th_style += f"vertical-align: {vertical_align};"
        # Set padding table data
        if random.random() < 0.8:
            pad_h_top = random.randint(1, 8)
            pad_h_bot = random.randint(1, 8)
            pad_h_left = random.randint(1, 15)
            pad_h_right = random.randint(1, 15)
        else:
            pad_h_top = pad_h_bot = pad_h_left = pad_h_right = 0

        th_style += f"padding-top: {pad_h_top}px;"
        th_style += f"padding-bottom: {pad_h_bot}px;"
        th_style += f"padding-right: {pad_h_right}px;"
        th_style += f"padding-left: {pad_h_left}px;"
        # Set word break
        # Text wrapping - break the line
        th_style += "word-break: break-word;"
        # Set limit size
        # Only need to set the height of the table header; don't need to set the height of the table data.
        if self.cell_max_height != 0:
            th_style += f"height: {random.randint(self.cell_max_height // 4, self.cell_max_height)}px;"
        if self.cell_max_width != 0:
            th_style += f"width: {random.randint(self.cell_max_width // 4, self.cell_max_width)}px;"
        # Set border style
        if 'th' in border_style:
            th_style += border_style['th']
        
        th_style += "}"
        return th_style

    def create_style(self):
        '''This function will dynamically create stylesheet. This stylesheet essentially creates our specific
        border types in tables'''
        # Create html style
        style = '<head><meta charset="UTF-8">'
        # Set font text, font size
        font_size = random.randint(1,3)
        list_fonts = ['Helvetica', 'Arial', 'Arial Black', 'Verdana', 'Tahoma', 
            'Trebuchet MS', 'Impact', 'Gill Sans', 'Times New Roman', 'Georgia',
            'Palatino', 'Baskerville', 'Andalé Mono', 'Courier', 'Lucida', 'Monaco',
            'Bradley Hand', 'Brush Script MT', 'Luminari', 'Comic Sans MS']
        font_text = random.choice(list_fonts)
        style += f'<font size="{font_size}" face="{font_text}" >'
        style += '<style>' 
        style += "html{background-color: white;}"
        # Set style table
        style += "table{"
        # Set the text's horizontal alignment
        style += "text-align:{};".format(
            random.choices(['left', 'right', 'center'], weights=[0.3, 0.2, 0.5], k=1)[0])
        # Using style border-collapse: collapse
        # Check visualization: https://www.w3schools.com/cssref/tryit.php?filename=trycss_border-collapse
        style += "border-collapse: collapse;"
        
        # # Set table style
        border_type = self.create_border_style()
        border_style = border_type['style']
        if 'table' in border_style:
            style += border_style['table']
        style += "}"
        td_style = self.create_table_data_style(border_style)
        style += td_style
        th_style =self.create_table_header_style(border_style)
        style += th_style
        
        # text effect
        self.underline = "underline"
        self.italic = "italicize"
        self.bold = "bolded"
        style += ".{} {{text-decoration: underline;}}".format(self.underline)
        style += ".{} {{font-style: italic;}}".format(self.italic)
        style += ".{} {{font-weight: bold;}}".format(self.bold)

        style += "</style></head>"
        return style

    def create_html(self):
        '''Depending on various conditions e.g. columns spanned, rows spanned, data types of columns,
        regular or irregular headers, tables types and border types, this function creates equivalent html
        script'''
        idcounter = 0
        structure = []
        temparr = ['td', 'th']
        html = "<!DOCTYPE html><html>"
        html += self.create_style()
        html += '<body><table>'
        # html += '<table style="width: 100%; table-layout:fixed;">'
        for r in range(self.no_of_rows):
            html += '<tr>'
            structure.append('<tr>')
            for c in range(self.no_of_cols):
                text_type = self.cell_types[r, c].decode('utf-8')
                row_span_value = int(self.row_spans_matrix[r, c])
                col_span_value = int(self.col_spans_matrix[r, c])
                htmlcol = temparr[['s', 'h'].index(self.headers[r][c].decode('utf-8'))]
                if self.cell_box_type == 'cell':
                    htmlcol += f' id={idcounter}'
                htmlcol_style = htmlcol
                # set color
                if ((col_span_value != 0) or (r, c) not in self.missing_cells) and random.random() < self.color_prob:
                    color = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
                    htmlcol_style += f' style="background-color: rgba({color[0]}, {color[1]}, {color[2]},1);"'
                
                # # Random text effect
                text_effect = random.choice(["", self.italic, self.bold, self.underline])
                htmlcol_style += f" class={text_effect}"

                if (row_span_value == -1):
                    continue
                elif (row_span_value > 0):
                    html += (f'<{htmlcol_style}' + ' rowspan=\"' + str(row_span_value)) + '">'

                    if row_span_value > 1:
                        structure.extend(('<td', f' rowspan=\"{row_span_value}\"', '>'))
                    else:
                        structure.append('<td>')
                else:
                    if col_span_value == -1:
                        continue
                    elif col_span_value == 0:
                        if (r, c) in self.missing_cells:
                            text_type = 't'
                    html += (f'<{htmlcol_style}' + ' colspan=\"' + str(col_span_value)) + '">'

                    if col_span_value > 1:
                        structure.extend(('<td', f' colspan=\"{col_span_value}\"', '>'))
                    else:
                        structure.append('<td>')
                if c == 0:
                    # First line must be set to English or word, not a number
                    text_type = 'e'
                txt = self.generate_random_text(text_type)
                if self.cell_box_type == 'text':
                    txt = f'<span id={idcounter}>{txt} </span>'
                idcounter += 1
                html += f'{txt}</{htmlcol}>'
                structure.append('</td>')

            html += '</tr>'
            structure.append('</tr>')
        html += "<table></body></html>"
        return html, structure, idcounter

    def create(self):
        '''This will create the complete table'''
        self.define_col_types()  # define the data types for each column
        self.generate_missing_cells()  # generate missing cells

        # Random span when drawing horizontal lines

        # first row span
        if self.max_span_col_count > 0 and random.random() < 0.5:
            self.make_first_row_spans()
        # # first col span
        if self.max_span_row_count > 0 and random.random() < 0.5:
            self.make_first_col_spans()

        # create equivalent html
        html, structure, idcounter = self.create_html()

        return idcounter, html, structure, self.border_type
