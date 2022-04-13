import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import time
import mplfinance as mpf
import requests
from datetime import datetime, timedelta

def findnthoccur(haystack, needle, n):
    parts= haystack.split(needle, n+1)
    if len(parts)<=n+1:
        return -1
    return len(haystack)-len(parts[-1])-len(needle)


st.title('Stock Tracking App for NASDAQ Mega Cap :heavy_dollar_sign: Companies') #above $200B

st.markdown('\n')
st.markdown('\n')
st.markdown('\n')
    
#reading stock names from an excel file that I got from the NASDAQ website
name_doc = pd.read_csv(r'name_list.csv')
names = name_doc.iloc[:, 0:2]
names_list = ' '.join(names.iloc[:, 0].tolist())
names['combined'] = names.apply(lambda row: row.names + ' - ' + row.full_names, axis=1)


data=yf.download(tickers=names_list, period='1d', group_by='ticker')  

info_list=[]

latest_iteration = st.empty()
bar = st.progress(0)
i=0
t=time.strftime("%H:%M:%S, %m/%d/%Y ", time.localtime())

for item in names.iloc[:,0]:
    perchange=(data[item]['Close'][0]-data[item]['Open'][0])/data[item]['Open'][0]*100
    info_list.append([item, data[item]['Open'][0], data[item]['Close'][0], perchange, abs(perchange)])
    
    latest_iteration.text(f'Last updated Ticker {item}')
    bar.progress((i + 1)/39)
    i=i+1

latest_iteration.text(f'Loading data from Yahoo Finance...done at {t}!')    

if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(data.T)

action = st.selectbox('Find out the: ', ['biggest mover', 'smallest mover'])

newdf = pd.DataFrame(info_list,
                       columns=['Name', 'Opening Price', 'Closing Price', 'Percentage Change', 'Absolute percentage change'])

biggest_mover = names.iloc[newdf['Absolute percentage change'].idxmax(), 2]
smallest_mover = names.iloc[newdf['Absolute percentage change'].idxmin(), 2]

if action=='biggest mover':
    
    if newdf.iloc[newdf['Absolute percentage change'].idxmax(), 3] > 0:
        emoji=':chart_with_upwards_trend:'
    else:
        emoji=':chart_with_downwards_trend:'
    
    st.write('The biggest mover in the last day is ', biggest_mover, ' with a ',
               '{:.2f}'.format(newdf.iloc[newdf['Absolute percentage change'].idxmax(), 3]),
              ' % change in its price.', emoji)
    

elif action=='smallest mover':
    
    if newdf.iloc[newdf['Absolute percentage change'].idxmin(), 3] > 0:
        emoji=':chart_with_upwards_trend:'
    else:
        emoji=':chart_with_downwards_trend:'
    
    st.write('The smallest mover in the last day is ', smallest_mover, ' with a ',
              '{:.2f}'.format(newdf.iloc[newdf['Absolute percentage change'].idxmin(), 3]),
             ' % change in its price.', emoji)
    
st.markdown('\n')
st.markdown('\n')
st.write(":black_large_square:")
st.markdown('\n')
st.markdown('\n')

st.write('Find all stocks with percentage change rates within your selected range')
dif=float(newdf['Percentage Change'].max()) - float(newdf['Percentage Change'].min())
slid = st.slider('Select a value for percentage change',
                  float(newdf['Percentage Change'].min()),
                  float(newdf['Percentage Change'].max()),
                  (float(newdf['Percentage Change'].min())+0.25*dif, float(newdf['Percentage Change'].max())-0.25*dif))
                  
st.write(newdf.loc[(newdf['Percentage Change'] >= slid[0]) & (newdf['Percentage Change'] <= slid[1]), ['Name', 'Opening Price', 'Closing Price', 'Percentage Change']].sort_values(by=['Percentage Change'], ascending=False, inplace=False))

st.markdown('\n')
st.markdown('\n')
st.write(":black_large_square:")
st.markdown('\n')
st.markdown('\n')                      


option = st.selectbox('Which MegaCap stock would you like to explore?', names.iloc[:, 2])

selected = str(names[names['combined']==str(option)].iloc[0,0])
stock_name=str(selected)
stock_name_long=str(names[names['combined']==str(option)].iloc[0,2])
sel = yf.Ticker(stock_name)


try:
    st.write('Sector: ', sel.info['sector'])
    st.write('Market Cap: $', '{:,d}'.format(sel.info['marketCap']))
    st.write('Previous Close: $', sel.info['regularMarketPreviousClose'])
    st.write('Open: $', sel.info['regularMarketOpen'])
    st.write('Average Volume in the last 10 days: ', '{:,d}'.format(sel.info['averageVolume10days'])) 

except:
    st.write('Company bio not available')

finally:
    per = st.selectbox('Choose the data period', ['5 days', '1 month', '6 months', '1 year'], index=1)
    per_dict={'5 days': '5d', '1 month': '1mo', '6 months': '6mo', '1 year': '1y'}
    
    mov = st.multiselect('Show moving average', ['3 day', '6 day', '9 day', '30 day'])
    mov_dict={'3 day': 3, '6 day': 6, '9 day': 9, '30 day':30}
    mov_list=[]
    for item in mov:
        mov_list.append(mov_dict[item])
    
    typ = st.selectbox('Choose chart type', ['Line', 'Candlestick', 'Open-High-Low-Close (OHLC)'], index=1)
    typ_dict={'Line':'line', 'Candlestick': 'candle', 'Open-High-Low-Close (OHLC)': 'ohlc'}
        
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.pyplot(mpf.plot(sel.history(period=per_dict[per], interval='1d'), mav=mov_list,
              type=typ_dict[typ], volume=True, show_nontrading=True, style='yahoo'))
          

datetime_object = datetime.now() - timedelta(days=7)
dat = datetime.strftime(datetime_object, "%Y-%m-%d")

url = 'http://newsapi.org/v2/everything?'

query_term=stock_name_long[findnthoccur(stock_name_long, ' ', 1):findnthoccur(stock_name_long, ' ', 2)]
final_query=stock_name+' OR '+query_term


paramet = {'qInTitle': final_query, 
       'from' : dat,
       'sortBy' : 'relevancy',
       'pageSize' : 3,
       'apiKey' : st.secrets['news_api_key'],
       'language' : 'en'
       }

respon = requests.get(url, params = paramet).json()

if respon['status']=='ok' and respon['totalResults']>0:
    st.subheader('Related news from the last week:')
    for i in range(min(3,respon['totalResults'])):
        tit = respon['articles'][i]['title']
        sourc = respon['articles'][i]['source']['name']
        link_url = respon['articles'][i]['url']
        
        txt_str = ':rolled_up_newspaper:  **'+tit+'**   from   ['+sourc+']('+link_url+')' 
        
        st.write(txt_str)
        

