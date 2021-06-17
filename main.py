from concurrent.futures import ProcessPoolExecutor
from jd_seckill import JdSeckill
from config import global_config
from jd_logger import logger
from timer import Timer
import time


def submit(sleep_time):
    jd_thread = JdSeckill()
    timer = Timer()
    timer.start()
    times = 0
    # jd_seckill.submit_cart_item() #提交部分信息，后发现可不使用
    # time.sleep(sleep_time)
    while True:
        jd_thread.get_vender_info()  # 获取供应商信息
        time.sleep(sleep_time)
        jd_thread.submit_order()  # 提交购物车中的全部商品订单
        time.sleep(sleep_time)
        times += 1
        if times >= 10:
            break


def seckill_by_proc_pool(work_count=3):
    """
    多线程进行抢购
    work_count:进程数量
    """
    sleep_time = float(global_config.getRaw('config', 'DEFAULT_SLEEP_TIME'))
    start_time = time.time()
    jd_seckill = JdSeckill()
    jd_seckill.login()
    jd_seckill.get_username()
    jd_seckill.add_cart()  # 添加对应id的商品到购物车
    logger.info("请检查是否已添加商品到购物车，如未添加则需要重新添加")

    with ProcessPoolExecutor(work_count) as pool:
        for i in range(work_count):
            pool.submit(submit(sleep_time))

    end_time = time.time()
    timdedelta = end_time - start_time
    print(f'共用秒数：{timdedelta}')


def run():
    sleep_time = float(global_config.getRaw('config', 'DEFAULT_SLEEP_TIME'))
    jd_seckill = JdSeckill()
    jd_seckill.login()
    jd_seckill.get_username()
    timer = Timer()
    timer.start()
    # jd_seckill.add_cart() #添加对应id的商品到购物车
    # logger.info("请检查是否已添加商品到购物车，如未添加则需要重新添加")
    times = 0
    while True:
        jd_seckill.get_vender_info()  # 获取供应商信息
        time.sleep(sleep_time)
        result = jd_seckill.submit_order()  # 提交购物车中的全部商品订单
        if result == None:
            print('Succeed!!!!!!!')
            break
        else:
            times += 1
            if times >= 1000:
                break
            else:
                time.sleep(0.5)
                continue


def main():
    seckill_by_proc_pool()  # 多线程抢购函数，会导致请求过于频繁而无法成功请求，因此注释掉,可以考虑不同账号多线程


if __name__ == "__main__":
    # main()
    run()
