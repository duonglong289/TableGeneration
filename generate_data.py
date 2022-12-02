import argparse
import sys
from TableGeneration.GenerateTable import GenerateTable
import multiprocessing as mp
from tqdm import tqdm
from datetime import date

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num', type=int, default=7000, help='the number of generate table')
    # output path
    parser.add_argument('--output', type=str, default='output/simple_table')  # data save path
    # courp path
    parser.add_argument('--ch_dict_path', type=str, default='dict/ch_news.txt')
    parser.add_argument('--en_dict_path', type=str, default='dict/en_corpus.txt')

    # table settings
    parser.add_argument('--border_type', type=str, default='full_line', 
                        choices=['full_line', 'partial_line', 'no_line'],
                        help='cell: use cell location as cell box; text: use location of text in cell as cell box')
    # cell box type
    parser.add_argument('--cell_box_type', type=str, default='cell',
                        help='cell: use cell location as cell box; text: use location of text in cell as cell box')
    # row and col
    parser.add_argument('--min_row', type=int, default=3, help='min rows in table')
    parser.add_argument('--max_row', type=int, default=40, help='max rows in table')
    parser.add_argument('--min_col', type=int, default=3, help='min cols in table')
    parser.add_argument('--max_col', type=int, default=20, help='max cols in table')
    # row and col span
    parser.add_argument('--max_span_row_count', type=int, default=5, help='max span rows')
    parser.add_argument('--max_span_col_count', type=int, default=5, help='max span cols')
    parser.add_argument('--max_span_value', type=int, default=7, help='max value in rowspan and colspan')
    # txts lens
    parser.add_argument('--min_txt_len', type=int, default=2, help='min number of char in cell')
    parser.add_argument('--max_txt_len', type=int, default=45, help='max number of char in cell')
    # color
    parser.add_argument('--color_prob', type=float, default=0, help='the prob of color cell')
    # cell size
    parser.add_argument('--cell_max_width', type=int, default=480, help='max width of cell')
    parser.add_argument('--cell_max_height', type=int, default=0, help='max height of cell')
    # windows size
    parser.add_argument('--browser_width', type=int, default=4800, help='width of browser')
    parser.add_argument('--browser_height', type=int, default=3600, help='height of browser')
    parser.add_argument('--browser', type=str, default='chrome', help='chrome or firefox')
    parser.add_argument('--num_workers', type=int, default=8, help='number of process worker')

    args = parser.parse_args()
    if args.browser == 'chrome' and sys.platform == 'darwin':
        print('firefox is recommend for Mac OS, bug you choice is chrome')
        sys.exit(0)
    return args


def gen(index):
    try:
        output = f'{args.output}_{date.today().strftime("%d%m%Y")}'
        t = GenerateTable(output=output,
                        ch_dict_path=args.ch_dict_path,
                        en_dict_path=args.en_dict_path,
                        cell_box_type=args.cell_box_type,
                        min_row=args.min_row,
                        max_row=args.max_row,
                        min_col=args.min_col,
                        max_col=args.max_col,
                        min_txt_len=args.min_txt_len,
                        max_txt_len=args.max_txt_len,
                        max_span_row_count=args.max_span_row_count,
                        max_span_col_count=args.max_span_col_count,
                        max_span_value=args.max_span_value,
                        color_prob=args.color_prob,
                        cell_max_width=args.cell_max_width,
                        cell_max_height=args.cell_max_height,
                        browser=args.browser,
                        browser_width=args.browser_width,
                        browser_height=args.browser_height,
                        border_type=args.border_type)

        t.gen_table_img_single(index)
        t.close()
    except KeyboardInterrupt:
        t.close()
    except Exception:
        t.close()


if __name__ == '__main__':
    global args
    args = parse_args()
    if args.num_workers == 0:
        t = GenerateTable(output=args.output,
                          ch_dict_path=args.ch_dict_path,
                          en_dict_path=args.en_dict_path,
                          cell_box_type=args.cell_box_type,
                          min_row=args.min_row,
                          max_row=args.max_row,
                          min_col=args.min_col,
                          max_col=args.max_col,
                          min_txt_len=args.min_txt_len,
                          max_txt_len=args.max_txt_len,
                          max_span_row_count=args.max_span_row_count,
                          max_span_col_count=args.max_span_col_count,
                          max_span_value=args.max_span_value,
                          color_prob=args.color_prob,
                          cell_max_width=args.cell_max_width,
                          cell_max_height=args.cell_max_height,
                          browser=args.browser,
                          browser_width=args.browser_width,
                          browser_height=args.browser_height,
                          border_type=args.border_type)

        t.gen_table_img(args.num)
        t.close()
    
    else:
        pool = mp.Pool(args.num_workers)
        output = list(tqdm(pool.imap_unordered(gen, range(args.num)),
                            total=args.num, desc="Generating "))
        pool.terminate()