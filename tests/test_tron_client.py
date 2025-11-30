"""
TRON API 客户端测试脚本

测试 src/clients/tron.py 的功能
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestTronAPIClient:
    """测试 TronAPIClient"""
    
    def test_import_client(self):
        """测试从新位置导入"""
        from src.clients.tron import TronAPIClient, AddressInfo
        assert TronAPIClient is not None
        assert AddressInfo is not None
    
    def test_address_info_dataclass(self):
        """测试 AddressInfo dataclass"""
        from src.clients.tron import AddressInfo
        
        info = AddressInfo(
            address="TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH",
            trx_balance=123.45,
            usdt_balance=50.00,
            recent_txs=[]
        )
        
        assert info.address == "TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH"
        assert info.format_trx() == "123.45"
        assert info.format_usdt() == "50.00"
    
    def test_get_explorer_links_tronscan(self):
        """测试 TronScan 浏览器链接生成"""
        from src.clients.tron import TronAPIClient
        
        address = "TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH"
        
        with patch('src.clients.tron.settings') as mock_settings:
            mock_settings.tron_explorer = 'tronscan'
            
            links = TronAPIClient.get_explorer_links(address)
            
            assert "overview" in links
            assert "txs" in links
            assert address in links["overview"]
            assert "tronscan" in links["overview"]
    
    def test_get_explorer_links_oklink(self):
        """测试 OKLink 浏览器链接生成"""
        from src.clients.tron import TronAPIClient
        
        address = "TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH"
        
        with patch('src.clients.tron.settings') as mock_settings:
            mock_settings.tron_explorer = 'oklink'
            
            links = TronAPIClient.get_explorer_links(address)
            
            assert "overview" in links
            assert "txs" in links
            assert address in links["overview"]
            assert "oklink" in links["overview"]


class TestTronAPIClientAsync:
    """测试 TronAPIClient 异步方法"""
    
    @pytest.mark.asyncio
    async def test_get_address_info_tronscan(self):
        """测试 TronScan API 调用"""
        from src.clients.tron import TronAPIClient, AddressInfo
        
        # Mock HTTP 响应
        mock_account_response = MagicMock()
        mock_account_response.status_code = 200
        mock_account_response.json.return_value = {
            'balance': 123450000,  # 123.45 TRX
            'withPriceTokens': [
                {
                    'tokenId': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
                    'balance': 50000000  # 50 USDT
                }
            ]
        }
        
        mock_tx_response = MagicMock()
        mock_tx_response.status_code = 200
        mock_tx_response.json.return_value = {
            'data': []
        }
        
        mock_client = AsyncMock()
        mock_client.get.side_effect = [mock_account_response, mock_tx_response]
        
        with patch('src.clients.tron.get_async_client', return_value=mock_client):
            with patch('src.clients.tron.settings') as mock_settings:
                mock_settings.tron_api_url = ''
                mock_settings.tron_api_key = None
                mock_settings.tron_explorer = 'tronscan'
                mock_settings.tron_timeout_secs = 10
                
                client = TronAPIClient()
                result = await client.get_address_info("TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH")
                
                assert result is not None
                assert isinstance(result, AddressInfo)
                assert result.trx_balance == 123.45
                assert result.usdt_balance == 50.0


class TestAddressQueryModuleIntegration:
    """测试 AddressQueryModule 与 TronAPIClient 集成"""
    
    def test_module_uses_tron_client(self):
        """测试模块使用 TronAPIClient"""
        from src.modules.address_query.handler import AddressQueryModule
        from src.clients.tron import TronAPIClient
        
        module = AddressQueryModule()
        
        assert hasattr(module, 'tron_client')
        assert isinstance(module.tron_client, TronAPIClient)


class TestBackwardCompatibility:
    """测试向后兼容性"""
    
    def test_explorer_module_still_works(self):
        """测试旧的 explorer 模块仍然可用"""
        try:
            from src.modules.address_query.explorer import explorer_links, get_tronscan_link
            
            address = "TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH"
            links = explorer_links(address)
            
            assert "overview" in links
            assert "txs" in links
        except ImportError:
            pytest.skip("explorer 模块已移除")
