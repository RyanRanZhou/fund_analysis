import streamlit as st
import requests
import json
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.models import ColumnDataSource, FactorRange, LabelSet
from bokeh.plotting import figure
from bokeh.transform import factor_cmap
from bokeh.palettes import Spectral10
# import matplotlib.pyplot as plt
from datetime import datetime
# import synonyms
# import jieba

# from utils import *

#############
# PAGE SET UP
#############

st.set_page_config(page_title="Fund Analysis",
                   page_icon="citic.jpg",
                   layout="wide",
                   initial_sidebar_state="expanded"
                   )


# st.markdown(
#     """
#     <style>
#     .reportview-container {
#         background: url("https://image.shutterstock.com/z/stock-vector-set-of-abstract-financial-chart-with-trend-line-graph-and-numbers-in-stock-market-mockup-template-737412658.jpg")
#     }
#     .sidebar.sidebar-content {
#         background: url("https://image.shutterstock.com/z/stock-vector-set-of-abstract-financial-chart-with-trend-line-graph-and-numbers-in-stock-market-mockup-template-737412658.jpg")
#     }
#     </style>
#     """, unsafe_allow_html=True
# )

def chicang_info(season, fund_code):
    url = 'http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code=' + fund_code + '&topline=10&year=' + season + '&month=&rt=0.521395962770737'
    df = pd.DataFrame(columns=['持仓排名', '股票代码', '股票名称', '占净值比例', '持股数（万股）', '持仓市值（万元）', '季度'])
    response = requests.get(url)
    results_page = BeautifulSoup(response.content, "html.parser")
    table_list = results_page.find_all('table', {'class': 'w782 comm tzxq'})
    if len(table_list) == 0:
        table_list = results_page.find_all('table', {'class': 'w782 comm tzxq t2'})
    flag = True
    for i in range(len(table_list)):
        season_cnt = re.search(r'(202[\d+])年([\d+])季度股票投资明细', results_page.find_all('h4')[i].get_text())[2]
        tr_list = table_list[i].find('tbody').find_all('tr')
        if flag and season == '2021':
            for tr in tr_list:
                td_list = tr.find_all('td')
                df = df.append(
                    {'持仓排名': td_list[0].get_text(), '股票代码': td_list[1].get_text(), '股票名称': td_list[2].get_text(),
                     '占净值比例': td_list[6].get_text(), '持股数（万股）': td_list[7].get_text(),
                     '持仓市值（万元）': td_list[8].get_text(), '季度': season + '-' + season_cnt}, ignore_index=True)

            flag = False
        else:
            for tr in tr_list:
                td_list = tr.find_all('td')
                df = df.append(
                    {'持仓排名': td_list[0].get_text(), '股票代码': td_list[1].get_text(), '股票名称': td_list[2].get_text(),
                     '占净值比例': td_list[4].get_text(), '持股数（万股）': td_list[5].get_text(),
                     '持仓市值（万元）': td_list[6].get_text(), '季度': season + '-' + season_cnt}, ignore_index=True)

    df['基金代码'] = fund_code
    df['基金经理'] = fund_list[fund_code][0]
    df['基金名称'] = fund_list[fund_code][1]
    return df


fund_list = {'001718': ('张宇帆', '工银物流产业股票'), '288001': ('佟巍', '华夏经典混合'), '530011': ('孙晟', '建信内生动力混合'),
             '001532': ('刘畅畅', '华安文体健康混合A'), '519704': ('刘鹏', '交银先进制造混合'), '519185': ('黄海', '万家精选混合'),
             '005228': ('陈健玮', '汇添富港股通专注成长'), '005583': ('杨添琦', '易方达港股通红利混合'), '010326': ('王诗瑶', '博时消费创新混合A')
             }


@st.cache
def load_chicang():
    chicang = pd.DataFrame(columns=['股票代码', '股票名称', '占净值比例', '持股数（万股）', '持仓市值（万元）'])
    for fund_code in fund_list.keys():
        chicang = chicang.append(chicang_info('2021', fund_code))
        chicang = chicang.append(chicang_info('2020', fund_code))
    # cleaning data
    chicang = chicang.reset_index()
    chicang.drop(['index'], axis=1, inplace=True)
    chicang['占净值比例'] = chicang['占净值比例'].map(lambda x: x.replace('%', '')).astype('float64')
    chicang = chicang.astype({'持仓排名': 'int32'})
    chicang = chicang[(chicang['季度'] == '2021-3') | (chicang['季度'] == '2021-2') | (chicang['季度'] == '2021-1') | (
                chicang['季度'] == '2020-4') | (chicang['季度'] == '2020-3')]
    return chicang


def jingzhi_info(fund_code):
    url = 'http://api.fund.eastmoney.com/f10/lsjz?fundCode=' + fund_code + '&pageIndex=1&pageSize=365'
    headers = {"Referer": "http://fundf10.eastmoney.com/"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Failure", response.status_code)
    response.encoding = 'UTF-8'  # 编码用utf-8
    df = pd.DataFrame(response.json()['Data']['LSJZList'])
    df['基金代码'] = fund_code
    df['基金经理'] = fund_list[fund_code][0]
    df['基金名称'] = fund_list[fund_code][1]
    return df


@st.cache
def load_jingzhi():
    # 爬取过去365个交易日的基金净值
    jingzhi = pd.DataFrame(columns=['FSRQ', 'DWJZ', 'LJJZ', 'SDATE', 'ACTUALSYI', 'NAVTYPE', 'JZZZL',
                                    'SGZT', 'SHZT', 'FHFCZ', 'FHFCBZ', 'DTYPE', 'FHSP'])
    for fund_code in fund_list.keys():
        jingzhi = jingzhi.append(jingzhi_info(fund_code))
    # cleaning data
    jingzhi = jingzhi.reset_index()
    jingzhi.drop(['index', 'SDATE', 'ACTUALSYI', 'NAVTYPE', 'FHFCZ', 'FHFCBZ', 'DTYPE', 'FHSP'], axis=1, inplace=True)
    jingzhi.rename(columns={'FSRQ': '净值日期', 'DWJZ': '单位净值', 'LJJZ': '累计净值', 'JZZZL': '日增长率',
                            'SGZT': '申购状态', 'SHZT': '赎回状态'}, inplace=True)
    jingzhi.replace('', np.nan, inplace=True)
    jingzhi = jingzhi.astype({'单位净值': 'float64', '累计净值': 'float64', '日增长率': 'float64'})
    jingzhi['净值日期'] = pd.to_datetime(jingzhi['净值日期'])
    jingzhi['季度'] = jingzhi.apply(
        lambda x: x['净值日期'].strftime("%Y") + '-' + str((int(x['净值日期'].strftime("%m")) - 1) // 3 + 1), axis=1)
    return jingzhi


def zcpz_info(fund_code):
    url = 'http://fundf10.eastmoney.com/zcpz_' + fund_code + '.html'
    table_list = pd.read_html(url, encoding='UTF-8')
    table_list[1]['基金代码'] = fund_code
    table_list[1]['基金经理'] = fund_list[fund_code][0]
    table_list[1]['基金名称'] = fund_list[fund_code][1]
    table_list[1]['报告期'] = table_list[1]['报告期'].map(lambda x: datetime.strptime(x, '%Y-%m-%d'))
    return table_list[1]


@st.cache
def load_zcpz():
    # 资产配置信息（股票/债券/现金比例）
    zcpz = pd.DataFrame(columns=['报告期', '股票占净比', '债券占净比', '现金占净比', '净资产（亿元）'])
    for fund_code in fund_list.keys():
        zcpz = zcpz.append(zcpz_info(fund_code))
    zcpz = zcpz.reset_index()
    zcpz.drop(['index'], axis=1, inplace=True)
    zcpz.replace('---', '0%', inplace=True)
    zcpz['股票占净比'] = zcpz['股票占净比'].map(lambda x: x.replace('%', '')).astype('float64')
    zcpz['债券占净比'] = zcpz['债券占净比'].map(lambda x: x.replace('%', '')).astype('float64')
    zcpz['现金占净比'] = zcpz['现金占净比'].map(lambda x: x.replace('%', '')).astype('float64')
    zcpz['上期净资产'] = zcpz.groupby('基金代码')['净资产（亿元）'].shift(-1)
    zcpz['上期股票占净比'] = zcpz.groupby('基金代码')['股票占净比'].shift(-1)
    return zcpz


def hypz_info(season, fund_code):
    url = 'http://api.fund.eastmoney.com/f10/HYPZ/?fundCode=' + fund_code + '&year=' + season
    headers = {"Referer": "http://fundf10.eastmoney.com/"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Failure", response.status_code)
    response.encoding = 'UTF-8'  # 编码用utf-8
    l = response.json()['Data']['QuarterInfos']
    totaldf = pd.DataFrame()
    for element in l:
        df = pd.DataFrame(element['HYPZInfo'])
        totaldf = totaldf.append(df)
    totaldf.reset_index(inplace=True)
    totaldf['index'] = totaldf['index'].map(lambda x: x + 1)
    return totaldf


@st.cache
def load_hypz():
    # 行业配置信息
    hypz = pd.DataFrame()
    for fund_code in fund_list.keys():
        hypz = hypz.append(hypz_info('2021', fund_code))
        hypz = hypz.append(hypz_info('2020', fund_code))
    # cleaning data
    hypz.drop(['SZ', 'ZJZBLDesc', 'ABBNAME', 'JJGSID',
               'FTYPE', 'FUNDTYP', 'FEATURE'], axis=1, inplace=True)
    hypz.rename(
        columns={'index': '权重排名', 'BZDM': '基金代码', 'FSRQ': '季度', 'HYDM': '行业代码', 'HYMC': '行业名称', 'SZDesc': '市值（万元）',
                 'ZJZBL': '占净值比例', 'SAMMVPCTNV': '上期占净值比例', 'PCTCP': '占净值比例变动', 'SHORTNAME': '基金名称'}, inplace=True)
    hypz['市值（万元）'] = hypz['市值（万元）'].map(lambda x: x.replace(',', ''))
    hypz = hypz.astype({'市值（万元）': 'float64', '占净值比例': 'float64'})
    season_dict = {'2021-09-30': '2021-3', '2021-06-30': '2021-2', '2021-03-31': '2021-1',
                   '2020-12-31': '2020-4', '2020-09-30': '2020-3', '2020-06-30': '2020-2', '2020-03-31': '2020-1'}
    hypz['季度'] = hypz['季度'].map(lambda x: season_dict[x])
    hypz.reset_index(drop=True)
    hypz['上期占净值比例'] = hypz.groupby(['基金代码', '行业代码'])['占净值比例'].shift(-1)
    hypz['占净值比例变动'] = hypz['占净值比例'] - hypz['上期占净值比例']
    return hypz


def get_description(fund_code, season, doc_code):
    #     print(fund_code, season)
    url = 'https://np-cnotice-fund.eastmoney.com/api/content/ann?client_source=web_fund&show_all=1&art_code=' + doc_code
    headers = {"Referer": "http://fundf10.eastmoney.com/"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Failure", response.status_code)
    response.encoding = 'UTF-8'  # 编码用utf-8
    report_text = response.json()['data']['notice_content']
    try:
        description = re.search(r'投资策略和运作分析([\s\S]*?)4.5', report_text)[1]
        description = description.replace('\n', '')
        description = description.replace('\r', '')
        description = description.replace(' ', '')
        return (description, season, fund_code, fund_list[fund_code][0], fund_list[fund_code][1])
    except:
        print(fund_code, season)
        return None


def get_report_link(fund_code):
    url = 'http://api.fund.eastmoney.com/f10/JJGG?&fundcode=' + fund_code + '&pageIndex=1&pageSize=20&type=3'
    headers = {"Referer": "http://fundf10.eastmoney.com/"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Failure", response.status_code)
    response.encoding = 'UTF-8'  # 编码用utf-8
    df = pd.DataFrame(response.json()['Data'])
    season_tick = ['2021-3', '2021-mid', '2021-2', '2021-1', '2020-abstract', '2020-year', '2020-4', '2020-3']
    return dict(zip(season_tick, list(df['ID'])))


@st.cache
def load_description():
    # 从研报中爬取投资策略与运作分析板块
    analysis_list = list()
    for fund_code in fund_list.keys():
        doc_dict = get_report_link(fund_code)
        for season, doc_code in doc_dict.items():
            if season in ('2021-mid', '2020-abstract', '2020-year'):
                continue
            analysis = get_description(fund_code, season, doc_code)
            if analysis is not None:
                analysis_list.append(get_description(fund_code, season, doc_code))
    analysis_df = pd.DataFrame(analysis_list, columns=['投资策略与运作分析', '季度', '基金代码', '基金经理', '基金名称'])
    return analysis_df




#########
# SIDEBAR
########
# st.sidebar.image('ubs3.png', width=200)
# st.sidebar.header('I want to :thinking_face:')
select_event = st.sidebar.selectbox('页面',
                                    ['主页', '基金详情页'])

if 'chicang_df' not in st.session_state:
    st.session_state['chicang_df'] = load_chicang()
if 'jingzhi_df' not in st.session_state:
    st.session_state['jingzhi_df'] = load_jingzhi()
if 'zcpz_df' not in st.session_state:
    st.session_state['zcpz_df'] = load_zcpz()
if 'hypz_df' not in st.session_state:
    st.session_state['hypz_df'] = load_hypz()
if 'analysis_df' not in st.session_state:
    st.session_state['analysis_df'] = load_description()
if 'sentiment_df' not in st.session_state:
    st.session_state['sentiment_df'] = pd.read_excel('sentiment_df.xlsx', index_col=0)

if st.button('更新数据'):
    st.write('正在爬取')
    st.session_state.chicang_df = load_chicang()
    st.session_state.jingzhi_df = load_jingzhi()
    st.session_state.zcpz_df = load_zcpz()
    st.session_state.hypz_df = load_hypz()
    st.session_state.analysis_df = load_description()
    st.session_state.sentiment_df = pd.read_excel('sentiment_df.xlsx', index_col=0)

if select_event == '主页':
    st.markdown(
        "<h1 style='text-align: center; font-size:31px;'>欢迎访问基金经理言行比较项目</h1>",
        unsafe_allow_html=True)
    st.markdown('___')
    st.markdown("<h2 style='text-align: Left; font-size:26px;'>项目背景</h2>",
                unsafe_allow_html=True)
    st.markdown('')

    st.markdown(
        '本项目选取了十位明星基金经理最热门的基金，试图通过基金经理季报中的\"言\"与其实际调仓的\"行\"进行对比')
    st.markdown('')
    st.markdown("<h2 style='text-align: Left; font-size:26px;'>使用说明</h2>",
                unsafe_allow_html=True)
    st.markdown('')

    st.markdown(
    '本web app从天天基金抓取基金数据信息，进入网页后自动加载，总加载时间约五分钟，'
    '加载完成后数据以cache形式缓存，该次web app访问全过程中不需再次等待，如需要再次刷新加载，请点击最上方**更新数据**按钮')
    st.markdown('')

else:
    fund_selectbox = st.sidebar.selectbox(
        "请选择想要查看的基金",
        ('张宇帆：工银物流产业股票', '佟巍：华夏经典混合', '孙晟：建信内生动力混合',
         '刘畅畅：华安文体健康混合', '刘鹏：交银先进制造混合', '黄海：万家精选混合',
         '陈健玮：汇添富港股通专注成长', '杨添琦：易方达港股通红利混合', '王诗瑶：博时消费创新混合A')
    )
    season_selectbox = st.sidebar.selectbox(
        "请选择想要查看的季度",
        ('2021-3', '2021-2', '2021-1', '2020-4')
    )
    col1, col2 = st.columns(2)
    col1.subheader(fund_selectbox)
    col2.subheader("季度：" + season_selectbox)
    season_dict = {'2021-3': '2021-09-30', '2021-2': '2021-06-30', '2021-1': '2021-03-31', '2020-4': '2020-12-31'}
    a = st.session_state.jingzhi_df[(st.session_state.jingzhi_df['基金名称'] == re.search(r'：(\w*)', fund_selectbox)[1]) & (
                st.session_state.jingzhi_df['季度'] == season_selectbox)]
    b = st.session_state.zcpz_df[(st.session_state.zcpz_df['基金名称'] == re.search(r'：(\w*)', fund_selectbox)[1]) & (
                st.session_state.zcpz_df['报告期'] == season_dict[season_selectbox])]
    col1, col2, col3 = st.columns(3)
    col1.metric("单位净值", a.iloc[0, 1], str(round((a.iloc[0, 1] / a.iloc[-1, 1] - 1) * 100, 2)) + "%")
    col2.metric("仓位比例", str(b.iloc[0, 1]) + "%", str(round(b.iloc[0, 1] - b.iloc[0, 9], 2)) + "%")
    col3.metric("净资产总值（亿元）", b.iloc[0, 4], str(round(b.iloc[0, 4] / b.iloc[0, 8] * 100 - 100, 2)) + "%")
    p = figure(title='基金单位净值走势', x_axis_label='日期', y_axis_label='单位净值')
    p.xaxis.formatter = DatetimeTickFormatter(days="%Y-%m-%d")
    p.line(a['净值日期'], a['单位净值'], legend_label='Trend', line_width=2)
    st.bokeh_chart(p, use_container_width=True)
    c = st.session_state.hypz_df[(st.session_state.hypz_df['基金名称'] == re.search(r'：(\w*)', fund_selectbox)[1]) & (
                st.session_state.hypz_df['季度'] == season_selectbox)]
    c = c.sort_values('占净值比例变动', ascending=False, key=lambda x: abs(x))[:5]
    c = c[abs(c['占净值比例变动'])>=1]



    st.markdown(
        "<h4 style='font-size:25px;'>行业配置比较</h4>",
        unsafe_allow_html=True)
    seasons = ['2021-3', '2021-2', '2021-1', '2020-4', '2020-3']
    # 行业配置

    st.markdown(
        "<h5 style='font-size:20px;'>NLP提取各行业倾向</h5>",
        unsafe_allow_html=True)
    d = st.session_state.sentiment_df[(st.session_state.sentiment_df['基金名称'] == re.search(r'：(\w*)', fund_selectbox)[1]) & (st.session_state.sentiment_df['季度'] == seasons[seasons.index(season_selectbox) + 1])]
    d = d.iloc[:,[3,4,12]]
    st.table(d)
    if st.button('点此查看上季度投资策略原文'):
        description = st.session_state.analysis_df[(st.session_state.analysis_df['基金名称'] == re.search(r'：(\w*)', fund_selectbox)[1]) & (st.session_state.analysis_df['季度'] == seasons[seasons.index(season_selectbox) + 1])].iloc[0]['投资策略与运作分析']
        st.markdown(description)

    e = pd.DataFrame(d.groupby('一级行业').mean()['pval_pos']).reset_index()
    e = e.rename(columns={'一级行业': "行业名称"})
    e['言'] = e['pval_pos'].apply(lambda x: 'Positive' if x>0.6 else 'Negative')

    st.markdown(
        "<h5 style='font-size:20px;'>实际调仓行业</h5>",
        unsafe_allow_html=True)
    st.markdown(
        "<h5 style='font-size:15px;'>选取仓位变动前五且绝对变动值超过总资产1%的行业</h5>",
        unsafe_allow_html=True)
    st.table(c.iloc[:,[4,6,8]])
    season_list = [season_selectbox, seasons[seasons.index(season_selectbox) + 1]]
    hangye_list = list(c['行业名称'].unique())
    x = [(hangye, season) for hangye in hangye_list for season in season_list]
    counts = sum(zip(list(c['占净值比例']), list(c['上期占净值比例'])), ())
    source = ColumnDataSource(
        data=dict(x=x, counts=counts, change=sum(zip(list(c['占净值比例变动']), list(c['占净值比例变动'])), ())))

    p = figure(x_range=FactorRange(*x), height=250, title="实际显著调仓行业",
               toolbar_location=None, tools="")
    p.vbar(x='x', top='counts', width=0.9, source=source, line_color="white",
           fill_color=factor_cmap('x', palette=Spectral10, factors=season_list, start=1, end=2))
    # labels = LabelSet(x='x', y='counts', text='change',
    #                   x_offset=100, y_offset=9, source=source, render_mode='canvas')
    p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.xaxis.major_label_orientation = 1
    p.xgrid.grid_line_color = None
    # p.add_layout(labels)
    st.bokeh_chart(p, use_container_width=True)

    st.markdown(
        "<h5 style='font-size:20px;'>言行比较</h5>",
        unsafe_allow_html=True)
    c = c.iloc[:,[4,6,8]]
    c['行'] = c['占净值比例变动'].apply(lambda x: 'Positive' if x>0 else 'Negative')
    st.table(c.merge(e, left_on = '行业名称', right_on = '行业名称', how = 'outer').iloc[:,[0,5,3]].fillna('Not Mentioned'))
