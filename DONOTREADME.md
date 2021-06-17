# Jd_Seckill

##### 非常感谢原作者 https://github.com/zhou-xiaojun/jd_mask 提供的代码
##### 也非常感谢 https://github.com/wlwwu/jd_maotai 进行的优化

## 主要功能

- 登陆京东商城（[www.jd.com](http://www.jd.com/)）
  - cookies登录 (需要自己手动获取)
- 秒杀预约后等待抢购
  - 定时开始自动抢购

## 运行环境

- [Python 3](https://www.python.org/)

## 第三方库

- 需要使用到的库已经放在requirements.txt，使用pip安装的可以使用指令  
`pip install -r requirements.txt`

## 使用教程  
#### 1. 网页扫码登录
#### 2. 填写config.ini配置信息 
(1)eid,和fp找个普通商品随便下单,然后在F12，控制台输入_JdTdudfp回车即可看到,这两个值可以填固定的 

(2)cookies_string,sku_id,DEFAULT_USER_AGENT
>这里注意每次扫码登陆后都需要重新获取cookies_string 
>sku_id为抢购商品id，暂不支持海外国际的商品
>DEFAULT_USER_AGENT默认ua，现为某版本edge的ua，可根据自己需要更改

(3)配置开始抢购的时间
>buy_time

#### 3.运行main.py 

