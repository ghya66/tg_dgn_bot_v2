"""
能量 API 接口测试脚本

测试 src/api/routes.py 中新增的能量 trxno API 对接接口

运行方式:
    pytest tests/test_energy_api.py -v
    
或单独运行某个测试:
    pytest tests/test_energy_api.py::test_get_energy_packages -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from fastapi.testclient import TestClient

# 导入被测试的模块
from src.api.app import create_api_app
from src.modules.energy.models import APIAccountInfo, APIPriceQuery, APIOrderResponse


# ==================== Fixtures ====================

@pytest.fixture
def app():
    """创建测试用 FastAPI 应用"""
    return create_api_app()


@pytest.fixture
def client(app):
    """创建同步测试客户端"""
    return TestClient(app)


@pytest.fixture
def mock_energy_client():
    """创建模拟的能量 API 客户端"""
    mock_client = MagicMock()
    
    # 模拟账户信息
    mock_client.get_account_info = AsyncMock(return_value=APIAccountInfo(
        username="test_user",
        balance_trx=1000.0,
        balance_usdt=500.0,
        frozen_balance=100.0
    ))
    
    # 模拟价格查询
    mock_client.query_price = AsyncMock(return_value=APIPriceQuery(
        energy_65k_price=3.0,
        energy_131k_price=6.0,
        package_price=3.6
    ))
    
    # 模拟购买能量
    mock_client.buy_energy = AsyncMock(return_value=APIOrderResponse(
        code=10000,
        msg="成功",
        data={"order_id": "TEST_ORDER_001"},
        order_id="TEST_ORDER_001"
    ))
    
    # 模拟购买笔数套餐
    mock_client.buy_package = AsyncMock(return_value=APIOrderResponse(
        code=10000,
        msg="成功",
        data={"order_id": "TEST_PKG_001"},
        order_id="TEST_PKG_001"
    ))
    
    # 模拟查询订单
    mock_client.query_order = AsyncMock(return_value=APIOrderResponse(
        code=10000,
        msg="订单存在",
        data={"status": "completed", "energy_amount": 65000}
    ))
    
    # 模拟激活地址
    mock_client.activate_address = AsyncMock(return_value=APIOrderResponse(
        code=10000,
        msg="激活成功",
        data={}
    ))
    
    return mock_client


# ==================== 测试用例 ====================

class TestEnergyPackagesAPI:
    """测试能量套餐相关 API"""
    
    def test_get_energy_packages(self, client):
        """测试获取能量套餐列表"""
        response = client.get("/api/energy/packages")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) >= 2  # 至少有 65k 和 131k 两个套餐
    
    def test_calculate_energy_price_65k(self, client):
        """测试计算 6.5 万能量价格"""
        response = client.post("/api/energy/calculate?energy_amount=65000")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["energy_amount"] == 65000
        assert data["data"]["price_trx"] > 0
    
    def test_calculate_energy_price_131k(self, client):
        """测试计算 13.1 万能量价格"""
        response = client.post("/api/energy/calculate?energy_amount=131000")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["energy_amount"] == 131000
        assert data["data"]["price_trx"] > 0


class TestEnergyConfigAPI:
    """测试能量配置 API"""
    
    def test_get_energy_config(self, client):
        """测试获取能量配置"""
        response = client.get("/api/energy/config")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "rent_address" in data["data"]
        assert "package_address" in data["data"]
        assert "flash_address" in data["data"]
        assert "api_configured" in data["data"]


class TestEnergyTrxnoAPI:
    """测试 trxno API 对接接口（需要 Mock）"""
    
    @pytest.fixture
    def auth_client(self, app, mock_energy_client):
        """创建带认证覆盖的测试客户端"""
        from src.api.auth import api_key_auth
        
        # 覆盖依赖项
        app.dependency_overrides[api_key_auth] = lambda: "test_api_key"
        
        with patch('src.api.routes.get_energy_api_client', return_value=mock_energy_client):
            yield TestClient(app)
        
        # 清理
        app.dependency_overrides.clear()
    
    @patch('src.api.routes.get_energy_api_client')
    def test_get_energy_prices(self, mock_get_client, client, mock_energy_client):
        """测试查询实时能量价格"""
        mock_get_client.return_value = mock_energy_client
        
        response = client.get("/api/energy/prices")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["energy_65k_price"] == 3.0
        assert data["data"]["energy_131k_price"] == 6.0
        assert data["data"]["source"] == "trxno.com"
    
    def test_get_energy_account(self, auth_client):
        """测试查询代理账户信息"""
        response = auth_client.get("/api/energy/account")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "test_user"
        assert data["data"]["balance_trx"] == 1000.0
    
    def test_buy_hourly_energy(self, auth_client):
        """测试购买时长能量"""
        response = auth_client.post(
            "/api/energy/buy-hourly",
            json={
                "receive_address": "TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH",
                "energy_amount": 65000,
                "rent_time": 1
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["order_id"] == "TEST_ORDER_001"
    
    def test_buy_hourly_energy_invalid_amount(self, auth_client):
        """测试购买无效能量数量"""
        response = auth_client.post(
            "/api/energy/buy-hourly",
            json={
                "receive_address": "TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH",
                "energy_amount": 50000,  # 无效数量
                "rent_time": 1
            }
        )
        
        assert response.status_code == 400
        # FastAPI HTTPException 可能返回 detail 或其他格式
        resp_json = response.json()
        error_msg = resp_json.get("detail", str(resp_json))
        assert "65000" in error_msg or "131000" in error_msg
    
    def test_buy_energy_package(self, auth_client):
        """测试购买笔数套餐"""
        response = auth_client.post(
            "/api/energy/buy-package",
            json={"receive_address": "TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["order_id"] == "TEST_PKG_001"
    
    def test_query_energy_order(self, auth_client):
        """测试查询能量订单"""
        response = auth_client.get("/api/energy/orders/TEST_ORDER_001")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["order_id"] == "TEST_ORDER_001"
    
    def test_activate_address(self, auth_client):
        """测试激活地址"""
        response = auth_client.post(
            "/api/energy/activate",
            json={"target_address": "TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["target_address"] == "TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH"


class TestEnergyAPIErrorHandling:
    """测试 API 错误处理"""
    
    @patch('src.api.routes.get_energy_api_client')
    def test_api_error_handling(self, mock_get_client, client):
        """测试 API 错误处理"""
        mock_client = MagicMock()
        mock_client.query_price = AsyncMock(side_effect=Exception("API 连接失败"))
        mock_get_client.return_value = mock_client
        
        response = client.get("/api/energy/prices")
        
        assert response.status_code == 500
        # FastAPI 返回的错误格式
        error_detail = response.json().get("detail", response.json().get("error", ""))
        assert "API 连接失败" in str(error_detail) or response.status_code == 500


# ==================== 集成测试（需要真实配置）====================

class TestEnergyAPIIntegration:
    """
    集成测试 - 需要真实的 trxno.com 账号配置
    
    运行前请确保 .env 中配置了:
    - ENERGY_API_USERNAME
    - ENERGY_API_PASSWORD
    """
    
    @pytest.mark.skip(reason="需要真实 API 配置")
    def test_real_get_prices(self, client):
        """真实测试获取价格"""
        response = client.get("/api/energy/prices")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        print(f"实时价格: {data['data']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
