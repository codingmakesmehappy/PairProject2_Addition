import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool, Manager
from requests.exceptions import ConnectionError
from functools import partial
from lxml import etree
import re
import time
headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}

def geturl(url,prelink):
    response = requests.get(url,headers=headers)
    text = response.text
    html = etree.HTML(text)
    links = html.xpath('//dt/a//@href')
    urls = []
    for link in links:
        url = prelink + link
        urls.append(url)
    return urls

def crawl(locker,data,prelink,url):
    try:
        response = requests.get(url,headers=headers)
        text = response.text
        pdfs,abstracts,authors,titles,books,months,years=data

        html=etree.HTML(text)
        author=html.xpath('//i/text()')[0]
        pdf = html.xpath('//a[contains(text(),"pdf")]/@href')[0]
        pdf = prelink + pdf[6:]
        abstract=html.xpath('//div[@id="abstract"]/text()')[0]
        abstract=abstract[1:]
        
        soup=BeautifulSoup(text,'lxml')
        detail=soup.find(class_="bibref")

        regex='(\w+) = {([\S\xa0 ]+)}'
        results = re.findall(regex,detail.getText())
        title = results[1][1]
        book = results[2][1]
        month = results[3][1]
        year = results[4][1]
        locker.acquire()  #获取锁

        authors.append(author)
        pdfs.append(pdf)
        abstracts.append(abstract)
        titles.append(title)
        books.append(book)
        months.append(month)
        years.append(year)
        
        locker.release()
    except ConnectionError:
        print('Error!',url)
    finally:
        print(url,'successed')

if __name__ == '__main__':
    start = time.clock()
    url='http://openaccess.thecvf.com/CVPR2018.py'
    prelink='http://openaccess.thecvf.com/'
    urls=geturl(url,prelink)

    pool = Pool(processes=32)
    manager = Manager()
    locker = manager.Lock()

    authors=manager.list()
    pdfs=manager.list()
    abstracts=manager.list()
    titles=manager.list()
    books=manager.list()
    months=manager.list()
    years = manager.list()

    data = (pdfs,abstracts,authors,titles,books,months,years)

    p_crawl = partial(crawl,locker,data,prelink)
    pool.map(p_crawl,urls)

    elapsed = (time.clock()-start)
    print("Time used: ",elapsed)

    with open('alldata.txt', 'w', encoding='utf-8') as file:
        for i in range(len(titles)):
            file.write(str(i) + '\n')
            file.write('Title: '  + titles[i] + '\n')
            file.write('Authors: ' + authors[i] + '\n')
            file.write('Abstract: ' + abstracts[i] + '\n')
            file.write('Book: ' + books[i] + '\n')
            file.write('PDF: ' + pdfs[i] + '\n')
            file.write('Year: ' + years[i] + '\n')
            file.write('Month: ' + months[i])
            file.write('\n\n')
    