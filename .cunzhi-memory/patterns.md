# 常用模式和最佳实践

- HTTP优化完成：1.统一超时配置(api_timeout_default_secs/okx_timeout_secs/tron_timeout_secs) 2.全局HTTP连接池复用(src/common/http_client.py) 3.只读请求重试机制(src/common/http_utils.py的get_with_retry函数) 4.Bot生命周期集成(启动初始化/停止关闭) 5.测试覆盖86/86通过
