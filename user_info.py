import os
import random
import string
import pickle
import asyncio


class Session(object):
    class UserNames(object):
        """这个类是用来创建随机用户名，并将所有生成的保存到本地"""

        def __init__(self, path='names.pkl'):
            self.path = path
            if not os.path.exists(self.path):
                self.save_names([])

        def get_names(self):
            with open(self.path, 'rb') as f:
                names = pickle.load(f)
            return names, os.path.getmtime(self.path)

        async def append(self, name, ticket):
            names, mtime = self.get_names()
            # 根据修改时间判断用户名是否改变（乐观锁）
            if ticket == mtime:
                names.append(name)
                return self.save_names(names)
            return await self.get_random_name()

        def remove(self, name):
            names, mtime = self.get_names()
            names.remove(name)
            return self.save_names(names)

        def save_names(self, names):
            with open(self.path, 'wb') as f:
                pickle.dump(names, f)
            return True

        async def get_random_name(self):
            get_upper = lambda: random.choice(string.ascii_uppercase)
            name = get_upper() + get_upper() + '%04d' % random.randint(0, 9999)
            names, mtime = self.get_names()
            if name in names:
                return await self.get_random_name()
            res = await self.append(name, mtime)
            if res:
                return name
            return await self.get_random_name()


def test_run(count=10000):
    """以下是测试并发10000次，随机生成用户名的时间以及并发产生的用户名是否满足需求"""
    import time
    st = time.time()
    username = Session.UserNames()
    old_names, mtime = username.get_names()
    # 异步生成10000次并发
    test_count = count
    res = asyncio.ensure_future(asyncio.wait([username.get_random_name() for i in range(test_count)]))
    # 等待结果完成
    loop = asyncio.get_event_loop()
    loop.run_until_complete(res)
    loop.close()
    # 打印运行时间
    print(time.time() - st)
    names, mtime = username.get_names()
    # 判断运行情况
    assert (len(names) == len(set(names)))
    assert len(names) == len(old_names) + test_count
    print(len(names))


if __name__ == '__main__':
    test_run(10000)
