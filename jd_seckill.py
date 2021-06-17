import lxml
from config import global_config
from jd_logger import logger
from timer import Timer
import requests
import random
import time
import util
import sys

class JdSeckill(object):
  def __init__(self):
    #初始化信息
    self.session = util.get_session()
    self.sku_id = global_config.getRaw('config', 'sku_id')
    self.buy_num = global_config.getRaw('config', 'buy_num')
    self.vender = '[]' #默认供应商为空
    self.sopNotPutInvoice = 'false' #默认此逻辑值为false，具体含义可能与vender有关

    self.seckill_num = 2  #抢购并发线程数
    self.shipment_info = {} #存放物流信息
    self.seckill_init_info = {}
    self.seckill_url = {}
    self.seckill_order_data = {}
    self.timers = Timer()
    self.default_user_agent = global_config.getRaw('config', 'DEFAULT_USER_AGENT')

  def wati_some_time(self):
      time.sleep(random.randint(100, 300) / 1000)

#初始化账号登录
  def login(self):
      for flag in range(1, 3):
          try:
              targetURL = 'https://order.jd.com/center/list.action'
              payload = {
                  'rid': str(int(time.time() * 1000)),
              }
              resp = self.session.get(
                  url=targetURL, params=payload, allow_redirects=False)
              if resp.status_code == requests.codes.OK:
                  logger.info('校验是否登录[成功]')
                  logger.info('用户:{}'.format(self.get_username()))
                  return True
              else:
                  logger.info('校验是否登录[失败]')
                  logger.info('请重新输入cookie')
                  time.sleep(1)
                  continue
          except Exception as e:
              logger.info('第【%s】次失败请重新获取cookie', flag)
              time.sleep(1)
              continue
      sys.exit(1)

  def get_username(self):
      """
      获取用户信息
      """
      url = 'https://passport.jd.com/user/petName/getUserInfoForMiniJd.action'
      payload = {
          'callback': 'jQuery'.format(random.randint(1000000, 9999999)),
          '_': str(int(time.time() * 1000)),
      }
      headers = {
          'User-Agent': self.default_user_agent,
          'Referer': 'https://order.jd.com/center/list.action',
      }

      resp = self.session.get(url=url, params=payload, headers=headers)

      try_count = 5
      while not resp.text.startswith("jQuery"):
          try_count = try_count - 1
          if try_count > 0:
              resp = self.session.get(url=url, params=payload, headers=headers)
          else:
              break
          self.wati_some_time()
      # 响应中包含了许多用户信息，现在在其中返回昵称
      return util.parse_json(resp.text).get('nickName')


#添加商品到购物车
  def add_cart(self):
    """
    将抢购商品添加到购物车，部分抢购商品会已经添加到购物车，此种情况有待解决
    :return: Boolean,是否成功添加到购物车
    """
    url = 'https://cart.jd.com/gate.action'
    params = {
      'pcount': '1', #添加的数量，默认为1
      'ptype': '1', #?
      'pid': self.sku_id,
    }
    headers = {
      'User-Agent': self.default_user_agent,
      'Referer': 'https://item.jd.com/',
    }
    response = self.session.get(url=url, headers=headers, params=params)
    print(response)


#获取并处理物流信息，从购物车提交商品订单信息到京东服务器，该部分暂时发现可以省略
  def submit_cart_item(self):
    """
    提交购物车中的商品，不确定是否支持多件商品
    """
    logger.info("尝试获取账号物流信息")
    self.get_shipment_info()
    logger.info("成功获取账号物流信息")
    logger.info("尝试设置收货人名单")
    self.setup_consignee()
    logger.info("成功设置收货人名单")
    logger.info("尝试检查打开的收货人")
    self.check_consignee()
    logger.info("成功检查打开的收货人")
    logger.info("尝试获取额外物流信息")
    self.submit_shipment()
    logger.info("成功获取额外物流信息")
    logger.info("成功从购物车提交商品订单信息到京东服务器")

  def get_shipment_info(self):
    """
    获取账号对应的物流信息
    """
    url = 'https://trade.jd.com/shopping/dynamic/consignee/getConsigneeList.action'
    headers = {
      'referer': 'https://cart.jd.com/',
      'user-agent': self.default_user_agent,
    }
    params = {
      'charset': 'UTF-8',
      'callback': 'jQuery'.format(random.randint(1000000, 9999999)),
      '_': str(int(time.time() * 1000)),
    }
    response = self.session.get(url, headers=headers, params=params)
    data = util.parse_list(response.text)
    if data.get('id') != None:
      self.shipment_info = {
        'id': data.get('id'),
        'newId': data.get('newId'),
        'provinceId': data.get('provinceId'),
        'cityId': data.get('cityId'),
        'countyId': data.get('countyId'),
        'townId': data.get('townId'),
      }
    else:
      return self.get_shipment_info()
  
  def setup_consignee(self):
    """
    设置收货人名单
    """
    url = 'https://trade.jd.com/shopping/dynamic/consignee/consigneeList.action'
    headers = {
      'origin': 'https://trade.jd.com',
      'referer': 'https://cart.jd.com/',
      'user-agent': self.default_user_agent,
    }
    data = {
      'consigneeParam.newId': self.shipment_info['newId'],
      'consigneeParam.addType': '0', #?
      'consigneeParam.userSmark': '1000000000000000000000000000011500000000000000000000001000000000000000000000000000000000000000000000', #???
      'presaleStockSign': self.buy_num,
    }
    response = self.session.post(url, headers=headers, data=data)

  def check_consignee(self):
    """
    检查打开的收货人
    """
    url = 'https://trade.jd.com/shopping/dynamic/consignee/checkOpenConsignee.action'
    headers = {
      'origin': 'https://trade.jd.com',
      'user-agent': self.default_user_agent,
      'referer': 'https://trade.jd.com/shopping/order/getOrderInfo.action',
    }
    data = {
      'consigneeParam.provinceId': self.shipment_info['provinceId'], #省份id,2为上海
      'consigneeParam.cityId': self.shipment_info['cityId'], #城市id
      'consigneeParam.countyId': self.shipment_info['countyId'], #地址信息
      'consigneeParam.townId': self.shipment_info['townId'], #地址信息
      'presaleStockSign': self.buy_num,
    }
    response = self.session.post(url, headers=headers, data=data)
    print(response)

  def get_vender_info(self):
    """
    获取供应商信息
    """
    url = 'https://trade.jd.com/shopping/dynamic/payAndShip/getVenderInfo.action'
    headers = {
      'origin': 'https://trade.jd.com',
      'user-agent': self.default_user_agent,
      'referer': 'https://trade.jd.com/shopping/order/getOrderInfo.action',
    }
    data = {
      'shipParam.payId': '4',
      'shipParam.pickShipmentItemCurr': 'false',
      'shipParam.onlinePayType': '0',
      'presaleStockSign': '1'
    }
    response = self.session.post(url, headers=headers, data=data)
    selector = lxml.etree.HTML(response.text)
    obj = selector.xpath('//div[@class="goods-tit"]/*/@id')
    if len(obj) >= 1:
      print(obj)
      self.vender = str([{"venderId":obj[0],"remark":""}])
      self.sopNotPutInvoice = 'true'

  def submit_shipment(self):
    """
    获取额外物流信息
    """
    url = 'https://trade.jd.com/shopping/dynamic/payAndShip/getAdditShipmentNew.action'
    headers = {
      'origin': 'https://trade.jd.com',
      'user-agent': self.default_user_agent,
      'referer': 'https://trade.jd.com/shopping/order/getOrderInfo.action',
    }
    data = {
      'paymentId': '4',
      'shipParam.reset311': '0',
      'resetFlag': '1000000000', #?!!!
      'shipParam.onlinePayType': '0',
      'typeFlag': '0', #?!!!!!
      'promiseTagType': '',
      'presaleStockSign': self.buy_num,
    }
    response = self.session.post(url, headers=headers, data=data)
    print(response)


#确认已提交的信息并生成付款订单
  def submit_order(self):
    """
    提交已核对的订单，缺少确认是否成功提交的返回值判断
    :return: Boolean,是否成功提交订单
    """
    print('start submit order')
    url = 'https://trade.jd.com/shopping/order/submitOrder.action'
    headers = {
      'user-agent': self.default_user_agent,
      'Referer': 'https://trade.jd.com/shopping/order/getOrderInfo.action',
    }
    data = {
      'overseaPurchaseCookies': '', #?
      'vendorRemarks': self.vender, #?!!!!
      'presaleStockSign': self.buy_num, #?
      'submitOrderParam.sopNotPutInvoice': self.sopNotPutInvoice, #?!!!!
      'submitOrderParam.trackID': 'TestTrackId', #?
      'submitOrderParam.ignorePriceChange': '0', #?
      'submitOrderParam.btSupport': '0', #?
      'submitOrderParam.eid': global_config.getRaw('config', 'eid'), #eid
      'submitOrderParam.fp':global_config.getRaw('config', 'fp'), #fp
      'submitOrderParam.jxj': '1', #?
    }
    params = {
      'presaleStockSign': self.buy_num, #前要加&的话是否需要添加参数?
    }
    response = self.session.post(url, headers=headers, params=params, data=data)
    datas = util.parse_json(response.text)
    logger.info(datas['message'])

if __name__ == "__main__":
  pass